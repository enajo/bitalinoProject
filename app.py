import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import os
import random
import time
import uuid
import pandas as pd
from functools import wraps
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage
import time
import bitalino
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.fft import rfft, rfftfreq
from io import BytesIO



# Flask application initialization
app = Flask(__name__)
matplotlib.use('Agg')  # Use a non-GUI backend for Matplotlib

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Ensure necessary directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'charts'), exist_ok=True)

# Temporary storage for the generated PDF
PDF_BUFFER = None


# Global constants
sampling_rate = 1000  # Hz (Sampling frequency)
mvc = 600  # Mock Maximum Voluntary Contraction

# Benchmarks (kg) for hand grip strength by age group
male_benchmarks = {"dominant": 45, "non_dominant": 40}  # Males 18–30 years
female_benchmarks = {"dominant": 25, "non_dominant": 20}  # Females 18–30 years


# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chart_path = db.Column(db.String(255), nullable=True)
    result_url = db.Column(db.String(255), nullable=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# EMG data summarization
def summarize_emg(data, num_categories=25):
    category_size = len(data) // num_categories
    data["Category"] = (data.index // category_size).astype(int)
    data["Category"] = data["Category"].clip(upper=num_categories - 1)
    grouped = data.groupby("Category").agg(
        mean_value=("A1", "mean"),
        max_value=("A1", "max"),
        min_value=("A1", "min"),
        std_value=("A1", "std"),
    ).reset_index()
    return grouped

# Generate plot for EMG data summary
def plot_emg_summary(data):
    """
    Generates a plot for summarized EMG data and returns it as both Base64 and raw buffer.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data["Category"], data["mean_value"], label="Average Muscle Activation", color="blue", marker="o")
    ax.fill_between(data["Category"], data["min_value"], data["max_value"], color="lightblue", alpha=0.4, label="Activation Range (Min-Max)")
    ax.set_title("Summarized EMG Signal", fontsize=16)
    ax.set_xlabel("Category (Interval)", fontsize=12)
    ax.set_ylabel("EMG Signal (mV)", fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Save plot to a buffer for the PDF
    pdf_buf = io.BytesIO()
    plt.savefig(pdf_buf, format="png")
    pdf_buf.seek(0)

    # Convert plot to Base64 for HTML
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png")
    img_buf.seek(0)
    base64_chart = base64.b64encode(img_buf.getvalue()).decode("utf8")
    img_buf.close()
    plt.close(fig)

    return base64_chart, pdf_buf

def bandpass_filter(data, lowcut, highcut, fs, order=4):
    """
    Applies a bandpass filter to isolate the desired frequency range.

    Args:
        data (array-like): Input signal.
        lowcut (float): Lower cutoff frequency.
        highcut (float): Upper cutoff frequency.
        fs (float): Sampling frequency.
        order (int): Filter order.

    Returns:
        array-like: Filtered signal.
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype="band")
    return filtfilt(b, a, data)

# EMG analysis and feedback
def analyze_emg_with_feedback(file_path, gender="male", hand="dominant"):
    """
    Analyze EMG data and provide metrics and actionable feedback.

    Args:
        file_path (str): Path to the uploaded EMG data file.
        gender (str): Gender of the user ("male" or "female").
        hand (str): Hand type ("dominant" or "non_dominant").

    Returns:
        dict: Metrics and feedback for the user.
    """
    # Load the data
    data = pd.read_csv(file_path, skiprows=22, sep="\t", header=None)
    data = data.drop(columns=[7])  # Drop NaN column if present
    data.columns = ["nSeq", "I1", "I2", "O1", "O2", "A1", "A2"]

    # Extract and preprocess EMG data
    emg_data = data["A1"]
    filtered_emg = bandpass_filter(emg_data, 20, 450, sampling_rate)  # Use global `sampling_rate`
    absolute_emg = np.abs(filtered_emg)
    normalized_emg = absolute_emg / mvc

    # Calculate metrics
    overall_mean = normalized_emg.mean()  # RMS
    overall_peak = normalized_emg.max()  # Peak amplitude
    overall_min = normalized_emg.min()  # Resting activation
    signal_variability = normalized_emg.std()  # Signal variability

    # Frequency domain metrics
    freqs = rfftfreq(len(normalized_emg), d=1 / sampling_rate)  # Use global `sampling_rate`
    fft_values = np.abs(rfft(normalized_emg))
    median_freq = freqs[np.searchsorted(np.cumsum(fft_values), np.cumsum(fft_values)[-1] / 2)]
    mpf = np.sum(freqs * fft_values**2) / np.sum(fft_values**2)

    # Generate feedback
    benchmark = male_benchmarks if gender == "male" else female_benchmarks
    expected_strength = benchmark[hand]
    estimated_strength = overall_peak * expected_strength
    recovery_percentage = (estimated_strength / expected_strength) * 100

    if recovery_percentage < 50:
        feedback = "Significant improvement is needed. Strength training exercises are recommended."
    elif recovery_percentage < 75:
        feedback = "Progress is evident. Focus on endurance and consistency exercises."
    else:
        feedback = "Your grip strength is nearing the expected recovery target. Maintain consistency."

    # Return metrics and feedback
    return {
        "Peak Amplitude": overall_peak,
        "RMS": overall_mean,
        "Median Frequency": median_freq,
        "Mean Power Frequency": mpf,
        "Resting Activation": overall_min,
        "Signal Variability": signal_variability,
        "Recovery Percentage": recovery_percentage,
        "Feedback": feedback,
    }
# Generate PDF for EMG analysis
def generate_pdf(data, plot_buffer):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("EMG Analysis Summary Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Add the chart
    elements.append(Paragraph("Summarized EMG Signal Chart", styles["Heading2"]))
    elements.append(Spacer(1, 12))
    plot_image = PILImage.open(plot_buffer)
    plot_image.save("temp_plot.png")
    elements.append(Image("temp_plot.png", width=400, height=300))

    # Add the summary table
    elements.append(Paragraph("Summary Statistics", styles["Heading2"]))
    elements.append(Spacer(1, 12))
    table_data = [["Interval", "Average Activation (mV)", "Peak Activation (mV)", "Resting Activation (mV)", "Signal Variability (mV)"]]
    for _, row in data.iterrows():
        table_data.append([ 
            row["Category"],
            f"{row['mean_value']:.2f}",
            f"{row['max_value']:.2f}",
            f"{row['min_value']:.2f}",
            f"{row['std_value']:.2f}",
        ])
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([ 
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    pdf_buffer.seek(0)
    os.remove("temp_plot.png")
    return pdf_buffer

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# BITalino sensor MAC address
MAC_ADDRESS = '98:D3:71:FD:62:0B'
sensor = None

@app.route('/live_emg')
def live_emg():
    """
    Live EMG data acquisition page
    """
    return render_template('live_emg.html')

@socketio.on('connect_sensor')
def connect_sensor():
    """
    Connect to BITalino sensor
    """
    global sensor
    try:
        sensor = bitalino.BITalino(MAC_ADDRESS)
        sensor.start()
        emit('sensor_status', {'status': 'Connected to BITalino sensor'})
    except Exception as e:
        emit('sensor_status', {'status': f'Error connecting to sensor: {str(e)}'})

@socketio.on('start_acquisition')
def start_acquisition():
    """
    Start acquiring data from BITalino sensor
    """
    if sensor is None:
        emit('sensor_status', {'status': 'Sensor not connected'})
        return
    
    try:
        # Mimicking live data with mock values
        while True:
            emg_data = sensor.read(1)  # Read data from A1 (1 sample)
            emg_value = emg_data[0][0]  # Getting the EMG value from A1
            
            # Send the live data to frontend
            emit('live_data', {'value': emg_value})
            time.sleep(0.1)  # Simulating real-time data acquisition
    except Exception as e:
        emit('sensor_status', {'status': f'Error during data acquisition: {str(e)}'})

@socketio.on('stop_acquisition')
def stop_acquisition():
    """
    Stop acquiring data from BITalino sensor
    """
    if sensor:
        sensor.stop()
        emit('sensor_status', {'status': 'Data acquisition stopped'})
    else:
        emit('sensor_status', {'status': 'Sensor is not connected'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    user = User.query.get(session['user_id'])
    files = File.query.filter_by(user_id=user.id).all()
    return render_template('user_dashboard.html', user=user, files=files)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file uploaded!', 'danger')
        return redirect(url_for('user_dashboard'))

    file = request.files['file']
    if not file.filename or not allowed_file(file.filename):
        flash('Invalid file type or no file selected!', 'danger')
        return redirect(url_for('user_dashboard'))

    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Analyze the file for EMG metrics and feedback
    analysis_results = analyze_emg_with_feedback(file_path, gender="male", hand="dominant")

    # Load and summarize the data
    raw_data = pd.read_csv(file_path, skiprows=22, sep="\t", header=None)
    raw_data.columns = ["nSeq", "I1", "I2", "O1", "O2", "A1", "A2","Extra" ]
    summarized_data = summarize_emg(raw_data)

    # Generate the chart
    base64_chart, plot_buffer = plot_emg_summary(summarized_data)

    # Generate the PDF report
    global PDF_BUFFER
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("EMG Analysis Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Metrics Table
    table_data = [
        ["Metric", "Value"],
        ["Peak Amplitude (mV)", f"{analysis_results['Peak Amplitude']:.2f}"],
        ["RMS (mV)", f"{analysis_results['RMS']:.2f}"],
        ["Median Frequency (Hz)", f"{analysis_results['Median Frequency']:.2f}"],
        ["Mean Power Frequency (Hz)", f"{analysis_results['Mean Power Frequency']:.2f}"],
        ["Resting Activation (mV)", f"{analysis_results['Resting Activation']:.2f}"],
        ["Signal Variability (mV)", f"{analysis_results['Signal Variability']:.2f}"],
        ["Recovery Percentage (%)", f"{analysis_results['Recovery Percentage']:.1f}"],
    ]
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Feedback
    elements.append(Paragraph("Actionable Feedback:", styles["Heading2"]))
    elements.append(Paragraph(analysis_results["Feedback"], styles["BodyText"]))

    # Build the PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    PDF_BUFFER = pdf_buffer  # Save buffer globally for download

    # Save file details in the database
    result_url = f"/results/{filename}"
    new_file = File(
        filename=filename,
        user_id=session['user_id'],
        chart_path=base64_chart,  # Save the chart's base64 string
        result_url=result_url
    )
    db.session.add(new_file)
    db.session.commit()

    # Render the result page with metrics, feedback, and the chart
    return render_template(
        'result.html',
        metrics=analysis_results,
        base64_chart=base64_chart
    )

@app.route("/download")
def download_pdf():
    """
    Serve the generated PDF report for download.
    """
    global PDF_BUFFER
    if PDF_BUFFER:
        PDF_BUFFER.seek(0)  # Ensure the buffer is at the beginning
        return send_file(PDF_BUFFER, as_attachment=True, download_name="EMG_Report.pdf", mimetype="application/pdf")
    return "No report available. Please upload a file first.", 400

# Process file and chart generation
def process_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    header_found = False
    data = []
    for line in lines:
        if header_found:
            if line.strip():
                try:
                    data.append([int(value) for value in line.split()])
                except ValueError:
                    continue
        elif line.strip() == '# EndOfHeader':
            header_found = True

    columns = ["nSeq", "I1", "I2", "O1", "O2", "A1"]
    data_dict = {col: [] for col in columns}
    for row in data:
        for idx, col in enumerate(columns):
            data_dict[col].append(row[idx])

    return data_dict

# Main entry point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
