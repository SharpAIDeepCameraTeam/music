import music21
import os
import random
import numpy as np
import note_seq
import tensorflow as tf
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.polyphony_rnn import polyphony_sequence_generator
from magenta.models.shared import sequence_generator_bundle
from note_seq import midi_io
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2

class MagentaGenerator:
    """Wrapper for Magenta's melody generation with music theory rules."""
    
    def __init__(self, model_name="attention_rnn"):
        self.model_name = model_name
        self.generator = self._create_generator()
        self.key = music21.key.Key('G')
        
        # Common chord progressions in classical music
        self.progressions = [
            ['I', 'IV', 'V', 'I'],      # Basic authentic cadence
            ['I', 'vi', 'IV', 'V'],     # Common pop progression
            ['I', 'V', 'vi', 'IV'],     # Royal road progression
            ['ii', 'V', 'I'],           # Two-five-one progression
        ]
        
        # Cadence patterns
        self.cadences = {
            'perfect': ['V', 'I'],
            'plagal': ['IV', 'I'],
            'half': ['I', 'V'],
            'deceptive': ['V', 'vi']
        }
    
    def _download_bundle(self):
        """Download the bundle for the specified model."""
        bundle_file = f"{self.model_name}.mag"
        if not os.path.exists(bundle_file):
            tf.io.gfile.copy(
                f"https://storage.googleapis.com/magentadata/models/melody_rnn/{self.model_name}.mag",
                bundle_file
            )
        return bundle_file
    
    def _create_generator(self):
        """Create a MelodyRNN generator."""
        bundle_file = self._download_bundle()
        bundle = sequence_generator_bundle.read_bundle_file(bundle_file)
        generator_map = melody_rnn_sequence_generator.get_generator_map()
        generator = generator_map[self.model_name](checkpoint=None, bundle=bundle)
        generator.initialize()
        return generator
    
    def generate_melody(self, length=32, temperature=1.0):
        """Generate a melody using Magenta with music theory constraints."""
        # Create an empty sequence
        steps_per_quarter = 4
        qpm = 120
        primer_sequence = music_pb2.NoteSequence()
        primer_sequence.tempos.add(qpm=qpm)
        primer_sequence.ticks_per_quarter = steps_per_quarter
        
        # Generate the sequence
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = temperature
        generator_options.generate_sections.add(
            start_time=0,
            end_time=length
        )
        
        sequence = self.generator.generate(primer_sequence, generator_options)
        return sequence
    
    def apply_music_theory(self, sequence, style='lyrical'):
        """Apply music theory rules to the generated sequence."""
        stream = music21.stream.Stream()
        
        # Convert sequence to music21 notes
        notes = []
        for note in sequence.notes:
            if style == 'lyrical':
                # Add legato articulation
                n = music21.note.Note(note.pitch)
                n.duration = music21.duration.Duration(note.end_time - note.start_time)
                if random.random() < 0.7:  # 70% chance of legato
                    n.articulations.append(music21.articulations.Legato())
                notes.append(n)
            else:
                # More rhythmic style
                n = music21.note.Note(note.pitch)
                n.duration = music21.duration.Duration(note.end_time - note.start_time)
                if random.random() < 0.4:  # 40% chance of staccato
                    n.articulations.append(music21.articulations.Staccato())
                notes.append(n)
        
        # Add dynamics
        for i, note in enumerate(notes):
            if i % 16 == 0:  # Every 4 measures
                dynamic = random.choice(['p', 'mp', 'mf', 'f'])
                stream.append(music21.dynamics.Dynamic(dynamic))
            stream.append(note)
        
        return stream

def create_sequence_from_scratch():
    """Create a new musical sequence using Magenta with music theory."""
    score = music21.stream.Score()
    
    # Create Magenta generator
    magenta_gen = MagentaGenerator("attention_rnn")
    
    # Generate parts
    parts = {
        'violin1': {'style': 'lyrical', 'octave': 1},    # Lead violin
        'violin2': {'style': 'lyrical', 'octave': 0},    # Supporting violin
        'viola': {'style': 'lyrical', 'octave': -1},     # Viola
        'cello': {'style': 'rhythmic', 'octave': -2},    # Cello
        'bass': {'style': 'rhythmic', 'octave': -3}      # Bass
    }
    
    # Generate and process each part
    for part_name, settings in parts.items():
        # Generate base melody
        sequence = magenta_gen.generate_melody(
            length=32,
            temperature=1.0 if part_name == 'violin1' else 0.8
        )
        
        # Transpose sequence to appropriate octave
        for note in sequence.notes:
            note.pitch += (12 * settings['octave'])
            # Ensure notes stay in reasonable range
            while note.pitch < 36:  # Lower limit
                note.pitch += 12
            while note.pitch > 96:  # Upper limit
                note.pitch -= 12
        
        # Convert to music21 and apply music theory rules
        stream = magenta_gen.apply_music_theory(sequence, settings['style'])
        
        # Create part
        part = music21.stream.Part()
        
        # Add instrument
        if part_name == 'violin1':
            part.append(music21.instrument.Violin())
            part.partName = "Violin I"
        elif part_name == 'violin2':
            part.append(music21.instrument.Violin())
            part.partName = "Violin II"
        elif part_name == 'viola':
            part.append(music21.instrument.Viola())
            part.partName = "Viola"
        elif part_name == 'cello':
            part.append(music21.instrument.Violoncello())
            part.partName = "Violoncello"
        else:  # bass
            part.append(music21.instrument.Contrabass())
            part.partName = "Contrabass"
        
        # Add key and time signature
        part.append(music21.key.Key('G'))
        part.append(music21.meter.TimeSignature('4/4'))
        
        # Add notes from the stream
        for element in stream:
            part.append(element)
        
        # Add to score
        score.append(part)
    
    # Add metadata
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "Generated String Orchestra Piece"
    score.metadata.composer = "SoundWave Studios (via Magenta)"
    
    return score

def export_to_musicxml(score, output_path):
    """Export the score as MusicXML."""
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Add XML declaration and DOCTYPE
        xml_content = '<?xml version="1.0" encoding=\'UTF-8\' standalone=\'no\' ?>\n'
        xml_content += '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
        
        # Add metadata
        score.metadata = music21.metadata.Metadata()
        score.metadata.composer = 'SoundWave Studios'
        score.metadata.title = 'Generated String Orchestra Piece'
        
        # Add identification information
        score.metadata.encoder = 'SoundWave Studios'
        score.metadata.software = 'music21 v8.3.0 with Magenta'
        score.metadata.encodingDate = music21.metadata.DateSingle('2024')
        
        # Export to MusicXML
        temp_path = output_path + '.tmp'
        score.write('musicxml', fp=temp_path)
        
        # Read the exported file and add proper headers
        with open(temp_path, 'r') as f:
            content = f.read()
            # Remove existing XML declaration if present
            if content.startswith('<?xml'):
                content = '\n'.join(content.split('\n')[1:])
            # Write final file with proper headers
            with open(output_path, 'w') as out:
                out.write(xml_content + content)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        # Verify the file was created and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception("Failed to create MusicXML file or file is empty")
            
    except Exception as e:
        raise Exception(f"Error exporting to MusicXML: {str(e)}")
