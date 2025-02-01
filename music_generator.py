import music21
import os
import random
import numpy as np
import note_seq
import tensorflow as tf
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.drums_rnn import drums_rnn_sequence_generator
from magenta.models.shared import sequence_generator_bundle
from magenta.music import drums_lib
from magenta.music import sequences_lib
from note_seq import midi_io
from note_seq.protobuf import generator_pb2
from note_seq.protobuf import music_pb2

class EDMGenerator:
    """Generator for EDM music with Magenta."""
    
    def __init__(self):
        self.melody_model = "attention_rnn"
        self.drums_model = "drum_kit_rnn"
        self.melody_generator = self._create_melody_generator()
        self.drums_generator = self._create_drums_generator()
        
        # EDM-specific parameters
        self.bpm = 128  # Standard EDM tempo
        self.key = 'C'  # We'll use C minor for that EDM feel
        self.scale = music21.scale.MinorScale(self.key)
        
        # Common EDM chord progressions
        self.progressions = [
            ['i', 'VI', 'III', 'VII'],  # Epic progressive house
            ['i', 'v', 'VI', 'III'],    # Future bass style
            ['i', 'III', 'VII', 'VI'],  # Trance progression
        ]
        
        # EDM structure parameters
        self.section_length = 8  # 8 bars per section
        self.buildup_length = 4  # 4 bars for buildup
        
    def _download_bundle(self, model_name):
        """Download the bundle for the specified model."""
        bundle_file = f"{model_name}.mag"
        if not os.path.exists(bundle_file):
            if "drum" in model_name:
                url = f"https://storage.googleapis.com/magentadata/models/drums_rnn/{bundle_file}"
            else:
                url = f"https://storage.googleapis.com/magentadata/models/melody_rnn/{bundle_file}"
            tf.io.gfile.copy(url, bundle_file)
        return bundle_file
    
    def _create_melody_generator(self):
        """Create a MelodyRNN generator."""
        bundle_file = self._download_bundle(self.melody_model)
        bundle = sequence_generator_bundle.read_bundle_file(bundle_file)
        generator_map = melody_rnn_sequence_generator.get_generator_map()
        generator = generator_map[self.melody_model](checkpoint=None, bundle=bundle)
        generator.initialize()
        return generator
    
    def _create_drums_generator(self):
        """Create a DrumsRNN generator."""
        bundle_file = self._download_bundle(self.drums_model)
        bundle = sequence_generator_bundle.read_bundle_file(bundle_file)
        generator_map = drums_rnn_sequence_generator.get_generator_map()
        generator = generator_map[self.drums_model](checkpoint=None, bundle=bundle)
        generator.initialize()
        return generator
    
    def generate_edm_melody(self, length=32):
        """Generate an EDM-style melody."""
        steps_per_quarter = 4
        primer_sequence = music_pb2.NoteSequence()
        primer_sequence.tempos.add(qpm=self.bpm)
        primer_sequence.ticks_per_quarter = steps_per_quarter
        
        # Generate with high temperature for more variation
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = 1.2
        generator_options.generate_sections.add(
            start_time=0,
            end_time=length
        )
        
        sequence = self.melody_generator.generate(primer_sequence, generator_options)
        
        # Post-process for EDM style
        for note in sequence.notes:
            # Quantize to 16th notes
            note.start_time = round(note.start_time * 4) / 4
            note.end_time = round(note.end_time * 4) / 4
            # Add velocity variation for dynamics
            note.velocity = random.randint(80, 127)
        
        return sequence
    
    def generate_drum_groove(self, length=32):
        """Generate a drum groove using Magenta's drums model."""
        steps_per_quarter = 4
        primer_sequence = music_pb2.NoteSequence()
        primer_sequence.tempos.add(qpm=self.bpm)
        primer_sequence.ticks_per_quarter = steps_per_quarter
        
        # Generate with moderate temperature for groove consistency
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = 0.9
        generator_options.generate_sections.add(
            start_time=0,
            end_time=length
        )
        
        sequence = self.drums_generator.generate(primer_sequence, generator_options)
        
        # Post-process for EDM style
        drums_lib.add_drums(sequence, drums_lib.DEFAULT_DRUM_TYPE)
        return sequence

    def create_chromatic_buildup(self, start_pitch=60, measures=4):
        """Create a chromatic buildup with increasing rhythm intensity."""
        notes = []
        base_divisions = [2, 4, 8, 16]  # Rhythmic divisions per measure (increasing intensity)
        
        for measure in range(measures):
            divisions = base_divisions[measure]  # Get increasingly faster rhythms
            notes_per_beat = divisions // 4
            duration = 4.0 / divisions  # Quarter note = 1.0
            
            for beat in range(4 * notes_per_beat):
                # Calculate pitch (rising chromatic scale)
                current_pitch = start_pitch + (measure * 4) + (beat // notes_per_beat)
                
                # Create note
                note = music21.note.Note(current_pitch)
                note.duration = music21.duration.Duration(duration)
                note.volume.velocity = 80 + (measure * 10)  # Increasing velocity
                
                # Add effects based on position
                if beat % notes_per_beat == 0:
                    note.volume.velocity += 10  # Accent beats
                
                notes.append(note)
        
        return notes
    
    def create_repeating_pattern(self, sequence, pattern_length=2):
        """Create a repeating pattern from a sequence."""
        if not sequence.notes:
            return sequence
        
        # Extract the first pattern_length measures
        pattern_duration = pattern_length * 4.0  # 4 beats per measure
        pattern_notes = []
        
        for note in sequence.notes:
            if note.start_time < pattern_duration:
                pattern_notes.append(note)
        
        # Create repeating pattern
        total_measures = 8  # Total length of the section
        repeated_sequence = music_pb2.NoteSequence()
        repeated_sequence.tempos.add(qpm=self.bpm)
        repeated_sequence.ticks_per_quarter = sequence.ticks_per_quarter
        
        for measure in range(0, total_measures, pattern_length):
            for note in pattern_notes:
                new_note = repeated_sequence.notes.add()
                new_note.CopyFrom(note)
                new_note.start_time += measure * 4.0
                new_note.end_time += measure * 4.0
                
                # Add slight variations to velocity
                new_note.velocity = min(127, note.velocity + random.randint(-10, 10))
        
        return repeated_sequence
    
    def create_drum_buildup(self, measures=4):
        """Create a drum buildup with increasing intensity."""
        sequence = music_pb2.NoteSequence()
        sequence.tempos.add(qpm=self.bpm)
        sequence.ticks_per_quarter = 4
        
        # Define drum patterns with increasing intensity
        patterns = [
            # Measure 1: Basic kick and snare
            [(36, 0), (38, 2)],
            # Measure 2: Add hi-hats
            [(36, 0), (38, 2), (42, 0.5), (42, 1.5), (42, 2.5), (42, 3.5)],
            # Measure 3: Double time
            [(36, i/2) for i in range(8)] + [(42, i/4) for i in range(16)],
            # Measure 4: Roll
            [(38, i/4) for i in range(16)] + [(42, i/8) for i in range(32)]
        ]
        
        for measure, pattern in enumerate(patterns):
            for pitch, offset in pattern:
                note = sequence.notes.add()
                note.pitch = pitch
                note.start_time = measure * 4.0 + offset
                note.end_time = note.start_time + 0.25
                note.velocity = min(127, 80 + (measure * 15))  # Increasing velocity
        
        return sequence

def create_edm_track():
    """Create a complete EDM track with melody and drums."""
    score = music21.stream.Score()
    
    # Create EDM generator
    edm_gen = EDMGenerator()
    
    # Generate initial melody and drums
    melody_sequence = edm_gen.generate_edm_melody(length=32)
    drums_sequence = edm_gen.generate_drum_groove(length=32)
    
    # Create repeating sections
    melody_sequence = edm_gen.create_repeating_pattern(melody_sequence, pattern_length=2)
    drums_sequence = edm_gen.create_repeating_pattern(drums_sequence, pattern_length=2)
    
    # Convert melody sequence to music21
    melody_part = music21.stream.Part()
    melody_part.append(music21.instrument.ElectricPiano())  # Synth lead
    melody_part.append(music21.tempo.MetronomeMark(number=edm_gen.bpm))
    
    # Add main melody
    for note in melody_sequence.notes:
        n = music21.note.Note(note.pitch)
        n.duration = music21.duration.Duration(note.end_time - note.start_time)
        n.volume.velocity = note.velocity
        melody_part.append(n)
    
    # Add chromatic buildup
    buildup_notes = edm_gen.create_chromatic_buildup(start_pitch=60, measures=4)
    for note in buildup_notes:
        melody_part.append(note)
    
    # Convert drum sequence to music21
    drums_part = music21.stream.Part()
    drums_part.append(music21.instrument.BassDrum())  # EDM drums
    
    # Add main drums
    for note in drums_sequence.notes:
        # Map drum pitches to standard MIDI drum map
        if note.pitch in [36, 35]:  # Bass drum
            n = music21.note.Note(36, duration=music21.duration.Duration(0.25))
        elif note.pitch in [38, 40]:  # Snare
            n = music21.note.Note(38, duration=music21.duration.Duration(0.25))
        elif note.pitch in [42, 44, 46]:  # Hi-hat
            n = music21.note.Note(42, duration=music21.duration.Duration(0.25))
        else:  # Other percussion
            n = music21.note.Note(note.pitch, duration=music21.duration.Duration(0.25))
        
        n.volume.velocity = note.velocity
        drums_part.append(n)
    
    # Add drum buildup
    drum_buildup = edm_gen.create_drum_buildup(measures=4)
    for note in drum_buildup.notes:
        n = music21.note.Note(note.pitch, duration=music21.duration.Duration(0.25))
        n.volume.velocity = note.velocity
        drums_part.append(n)
    
    # Add parts to score
    score.append(melody_part)
    score.append(drums_part)
    
    # Add metadata
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "Generated EDM Track"
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
        score.metadata.title = 'Generated EDM Track'
        
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
