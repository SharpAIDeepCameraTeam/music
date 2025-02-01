import os
import music21
import random

def create_melody(key_obj, section_type, num_measures):
    """Create a melody section."""
    melody = []
    scale = key_obj.getScale()
    scale_pitches = [p for p in scale.pitches]
    
    # Different pitch patterns for A and B sections
    if section_type == 'A':
        # A section uses more stable scale degrees (1,3,5)
        main_pitches = [scale_pitches[i] for i in [0, 2, 4]]
    else:
        # B section uses more varied pitches
        main_pitches = [scale_pitches[i] for i in [1, 3, 5, 6]]
    
    for _ in range(num_measures):
        # Create a one-measure phrase
        beats_remaining = 4.0  # 4/4 time
        while beats_remaining > 0:
            # Choose duration: whole, half, quarter, or eighth notes
            duration = random.choice([4.0, 2.0, 1.0, 0.5])
            if duration > beats_remaining:
                duration = beats_remaining
                
            # Choose pitch
            if random.random() < 0.7:  # 70% chance of main pitches
                pitch = random.choice(main_pitches)
            else:
                pitch = random.choice(scale_pitches)
            
            # Create note
            note = music21.note.Note(pitch, quarterLength=duration)
            
            # Add dynamics for interest
            if duration >= 2.0:
                note.expressions.append(music21.expressions.Crescendo())
            
            melody.append(note)
            beats_remaining -= duration
            
    return melody

def create_sequence_from_scratch():
    """Create a new musical sequence from scratch."""
    score = music21.stream.Score()
    
    # Create parts for each instrument
    violin1 = music21.stream.Part()
    violin2 = music21.stream.Part()
    viola = music21.stream.Part()
    cello = music21.stream.Part()
    bass = music21.stream.Part()
    
    # Set time signature and key
    time_sig = music21.meter.TimeSignature('4/4')
    key = music21.key.Key('G')  # G major, good for strings
    
    # Add time signature and key to each part
    for part in [violin1, violin2, viola, cello, bass]:
        part.append(time_sig)
        part.append(key)
    
    # Create lead melody for Violin I (A section)
    melody_a = [
        ('G4', 2), ('B4', 2), ('D5', 2), ('G5', 2),  # Ascending G major
        ('A5', 3), ('G5', 1), ('E5', 2), ('D5', 2),  # Melodic line
        ('B4', 4), ('rest', 2), ('D5', 2),           # Rest and pickup
        ('G5', 2), ('F#5', 1), ('E5', 1), ('D5', 2), ('B4', 2)  # Descending line
    ]
    
    # B section melody (more dramatic)
    melody_b = [
        ('A5', 2), ('B5', 2), ('C6', 3), ('A5', 1),  # Higher register
        ('G5', 2), ('E5', 2), ('F#5', 3), ('D5', 1),  # Moving line
        ('E5', 2), ('G5', 2), ('F#5', 3), ('E5', 1),  # Tension building
        ('D5', 4), ('rest', 2), ('D5', 2)             # Resolution
    ]
    
    # Function to create harmony notes based on melody
    def create_harmony(melody_note, chord_type='major'):
        if melody_note == 'rest':
            return ['rest'] * 4
        note_obj = music21.note.Note(melody_note)
        if chord_type == 'major':
            intervals = [3, 5, 7]  # Major chord
        else:
            intervals = [3, 5, 7]  # Could be modified for minor
        harmony = []
        for interval in intervals:
            harmony_note = note_obj.transpose(interval)
            harmony.append(harmony_note.nameWithOctave)
        return harmony
    
    # Add notes to Violin I (lead)
    def add_melody_to_violin1(melody):
        for pitch, duration in melody:
            if pitch == 'rest':
                n = music21.note.Rest()
            else:
                n = music21.note.Note(pitch)
            n.duration.quarterLength = duration
            violin1.append(n)
    
    # Add harmony to other strings
    def add_harmony(melody, parts):
        for pitch, duration in melody:
            harmony = create_harmony(pitch if pitch != 'rest' else 'rest')
            for part, harm_pitch in zip(parts, harmony):
                if harm_pitch == 'rest':
                    n = music21.note.Rest()
                else:
                    n = music21.note.Note(harm_pitch)
                    # Make harmony slightly softer than melody
                    n.volume.velocity = 64
                n.duration.quarterLength = duration
                part.append(n)
    
    # Create A section
    add_melody_to_violin1(melody_a)
    add_harmony(melody_a, [violin2, viola, cello])
    # Bass plays root notes
    for pitch, duration in melody_a:
        if pitch == 'rest':
            n = music21.note.Rest()
        else:
            note_obj = music21.note.Note(pitch)
            bass_note = note_obj.transpose(-12)  # One octave down
            n = music21.note.Note(bass_note.nameWithOctave)
            n.volume.velocity = 72
        n.duration.quarterLength = duration
        bass.append(n)
    
    # Create B section
    add_melody_to_violin1(melody_b)
    add_harmony(melody_b, [violin2, viola, cello])
    # Bass continues with root notes
    for pitch, duration in melody_b:
        if pitch == 'rest':
            n = music21.note.Rest()
        else:
            note_obj = music21.note.Note(pitch)
            bass_note = note_obj.transpose(-12)
            n = music21.note.Note(bass_note.nameWithOctave)
            n.volume.velocity = 72
        n.duration.quarterLength = duration
        bass.append(n)
    
    # Repeat A section
    add_melody_to_violin1(melody_a)
    add_harmony(melody_a, [violin2, viola, cello])
    for pitch, duration in melody_a:
        if pitch == 'rest':
            n = music21.note.Rest()
        else:
            note_obj = music21.note.Note(pitch)
            bass_note = note_obj.transpose(-12)
            n = music21.note.Note(bass_note.nameWithOctave)
            n.volume.velocity = 72
        n.duration.quarterLength = duration
        bass.append(n)
    
    # Add dynamics
    for part in [violin1, violin2, viola, cello, bass]:
        f = music21.dynamics.Dynamic('f')
        part.insert(0, f)
    
    # Add parts to score
    score.append([violin1, violin2, viola, cello, bass])
    
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
        score.metadata.title = 'Orchestral Piece in ABA Form'
        
        # Add identification information
        score.metadata.encoder = 'SoundWave Studios'
        score.metadata.software = 'music21 v8.3.0'
        score.metadata.encodingDate = music21.metadata.DateSingle('2024')
        
        # Set part names
        part_names = [
            ("Violin I", "Vln. I"),
            ("Violin II", "Vln. II"),
            ("Viola", "Vla."),
            ("Violoncello", "Vc."),
            ("Contrabass", "Cb.")
        ]
        
        # Create part group for strings
        part_group = music21.layout.StaffGroup(
            [score.parts[i] for i in range(len(score.parts))],
            name='Strings',
            abbreviation='Str.',
            symbol='bracket'
        )
        score.insert(0, part_group)
        
        # Set part names and staff groups
        for part, (name, abbrev) in zip(score.parts, part_names):
            part.partName = name
            part.partAbbreviation = abbrev
            part.staffGroup = ['strings']
        
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
