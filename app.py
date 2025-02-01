from flask import Flask, send_file, jsonify
import os
from music_generator import create_sequence_from_scratch, export_to_musicxml
import tempfile

app = Flask(__name__)

# Ensure the uploads directory exists
os.makedirs('uploads', exist_ok=True)

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Orchestra Music Generator</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }
                button {
                    font-size: 18px;
                    padding: 10px 20px;
                    margin: 20px;
                    cursor: pointer;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                button:hover {
                    background-color: #45a049;
                }
                #status {
                    margin: 20px;
                    padding: 10px;
                }
            </style>
        </head>
        <body>
            <h1>Orchestra Music Generator</h1>
            <p>Generate a 30-measure orchestral piece in ABA form</p>
            <button onclick="generateMusic()">Generate Music</button>
            <div id="status"></div>
            
            <script>
                function generateMusic() {
                    const status = document.getElementById('status');
                    status.textContent = 'Generating music...';
                    
                    fetch('/generate')
                        .then(response => response.blob())
                        .then(blob => {
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'generated_music.xml';
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            status.textContent = 'Music generated successfully!';
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            status.textContent = 'Error generating music. Please try again.';
                        });
                }
            </script>
        </body>
    </html>
    '''

@app.route('/generate')
def generate():
    try:
        # Create a temporary file with .xml extension
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as tmp:
            # Generate the music score
            score = create_sequence_from_scratch()
            
            # Export to MusicXML
            export_to_musicxml(score, tmp.name)
            
            # Send the file with correct MIME type
            return send_file(
                tmp.name,
                mimetype='application/vnd.recordare.musicxml+xml',
                as_attachment=True,
                download_name='generated_music.xml'
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
