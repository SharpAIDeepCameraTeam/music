import os
import time
import traceback
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from music_generator import (
    parse_input_file,
    generate_music,
    harmonize_for_strings,
    export_to_musicxml
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mid', 'midi', 'musicxml', 'xml'}

# Available musical keys and time signatures
AVAILABLE_KEYS = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#',
                 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb',
                 'Am', 'Em', 'Bm', 'F#m', 'C#m', 'G#m', 'D#m',
                 'Dm', 'Gm', 'Cm', 'Fm', 'Bbm', 'Ebm', 'Abm']

TIME_SIGNATURES = ['4/4', '3/4', '6/8', '2/4', '5/4']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html',
                         keys=AVAILABLE_KEYS,
                         time_signatures=TIME_SIGNATURES)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        start_time = time.time()
        print("Starting music generation...")
        
        # Get parameters from form
        key = request.form.get('key', 'C')
        time_signature = request.form.get('time_signature', '4/4')
        tempo = float(request.form.get('tempo', 120))
        temperature = float(request.form.get('temperature', 1.0))
        
        print(f"Parameters: key={key}, time_signature={time_signature}, tempo={tempo}")
        
        # Check if file was uploaded
        if 'file' in request.files and request.files['file'].filename != '':
            print("Processing uploaded file...")
            file = request.files['file']
            if not allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid file type. Please upload a MIDI or MusicXML file.'
                }), 400
            
            # Save and process uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                input_sequence = parse_input_file(filepath)
            except Exception as e:
                print(f"Error parsing file: {str(e)}")
                print(traceback.format_exc())
                return jsonify({
                    'status': 'error',
                    'message': f'Error parsing file: {str(e)}'
                }), 400
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)  # Clean up uploaded file
        else:
            print("Generating from scratch...")
            input_sequence = None
        
        # Generate music
        print("Generating base music...")
        try:
            score = generate_music(
                input_sequence=input_sequence,
                key=key,
                time_signature=time_signature,
                tempo=tempo,
                temperature=temperature
            )
        except Exception as e:
            print(f"Error generating music: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Error generating music: {str(e)}'
            }), 500
        
        # Harmonize for string orchestra
        print("Harmonizing for strings...")
        try:
            full_score = harmonize_for_strings(score)
        except Exception as e:
            print(f"Error harmonizing: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Error harmonizing: {str(e)}'
            }), 500
        
        # Export to MusicXML
        print("Exporting to MusicXML...")
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.musicxml')
        try:
            export_to_musicxml(full_score, output_path)
            with open(output_path, 'r') as f:
                xml_content = f.read()
        except Exception as e:
            print(f"Error exporting to MusicXML: {str(e)}")
            print(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Error exporting to MusicXML: {str(e)}'
            }), 500
        
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Total processing time: {processing_time:.2f} seconds")
        
        return jsonify({
            'status': 'success',
            'xml_content': xml_content,
            'message': f'Music generated successfully in {processing_time:.1f} seconds!'
        })
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500

@app.route('/download', methods=['GET'])
def download_file():
    try:
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.musicxml')
        if not os.path.exists(output_path):
            return jsonify({
                'status': 'error',
                'message': 'No music has been generated yet. Please generate music first.'
            }), 404
        return send_file(
            output_path,
            as_attachment=True,
            download_name='string_arrangement.musicxml'
        )
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'Error downloading file: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
