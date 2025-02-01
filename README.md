# String Music Generator

A web application that generates string orchestra arrangements from MIDI or MusicXML melodies using Magenta and Music21.

## Features

- Upload MIDI or MusicXML files containing string melodies
- Generate musical continuations using Magenta's MelodyRNN model
- Create full string orchestra arrangements (violins, violas, cellos, basses)
- Export results as MusicXML files

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Upload a MIDI or MusicXML file containing a string melody

4. Click "Generate Music" to create your arrangement

5. Download the generated MusicXML file

## Technical Details

- Uses Magenta's MelodyRNN model for melody continuation
- Employs Music21 for music parsing and arrangement
- Implements a simple harmonization algorithm for string orchestra
- Built with Flask for the web interface

## File Structure

```
soundwave_music_gen/
├── app.py              # Flask application
├── music_generator.py  # Core music generation logic
├── requirements.txt    # Python dependencies
├── static/            # Static files
├── templates/         # HTML templates
│   └── index.html    # Main page template
└── uploads/          # Temporary file storage
```

## Dependencies

- magenta-gpu
- music21
- pretty-midi
- flask
- numpy
- tensorflow

## Notes

- Maximum file size: 16MB
- Supported file formats: MIDI (.mid, .midi) and MusicXML (.musicxml, .xml)
- Generated arrangements include parts for first violins, second violins, violas, cellos, and double basses
