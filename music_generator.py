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
    """Create a 30-measure ABA orchestral piece."""
    score = music21.stream.Score()
    
    # Create metadata
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "Orchestral Piece in ABA Form"
    
    # Fixed parameters
    key = music21.key.Key('C')
    time_sig = music21.meter.TimeSignature('4/4')
    tempo = music21.tempo.MetronomeMark(number=120)
    
    # Create sections (10 measures each for ABA form)
    section_A1 = create_melody(key, 'A', 10)
    section_B = create_melody(key, 'B', 10)
    section_A2 = create_melody(key, 'A', 10)
    
    # Combine all sections
    melody = section_A1 + section_B + section_A2
    
    # Create orchestra parts
    violin1 = music21.stream.Part()
    violin2 = music21.stream.Part()
    viola = music21.stream.Part()
    cello = music21.stream.Part()
    bass = music21.stream.Part()
    
    # Set instruments
    violin1.append(music21.instrument.Violin())
    violin2.append(music21.instrument.Violin())
    viola.append(music21.instrument.Viola())
    cello.append(music21.instrument.Violoncello())
    bass.append(music21.instrument.Contrabass())
    
    # Add key, time signature, and tempo to all parts
    for part in [violin1, violin2, viola, cello, bass]:
        part.append(key)
        part.append(time_sig)
        part.append(tempo)
    
    # Add melody to first violin
    for note in melody:
        violin1.append(note)
    
    # Create harmony parts
    current_time = 0
    for melody_note in melody:
        # Get the current chord tones based on the melody note
        scale_deg = key.getScale().getScaleDegreeFromPitch(melody_note.pitch)
        
        # Create harmony notes
        if scale_deg in [1, 4, 5]:  # Major chord
            intervals = [3, 7]  # Third and fifth
        else:  # Minor chord
            intervals = [4, 7]  # Minor third and fifth
        
        # Add harmony notes to other parts
        v2_note = melody_note.transpose(-intervals[0])
        viola_note = melody_note.transpose(-intervals[1])
        cello_note = melody_note.transpose(-12)  # Octave below
        bass_note = melody_note.transpose(-24)  # Two octaves below
        
        # Ensure notes are in appropriate ranges
        while v2_note.pitch.midi < 55:  # G3
            v2_note = v2_note.transpose(12)
        while viola_note.pitch.midi < 48:  # C3
            viola_note = viola_note.transpose(12)
        while cello_note.pitch.midi < 36:  # C2
            cello_note = cello_note.transpose(12)
        while bass_note.pitch.midi < 28:  # E1
            bass_note = bass_note.transpose(12)
        
        # Add notes to parts
        violin2.insert(current_time, v2_note)
        viola.insert(current_time, viola_note)
        cello.insert(current_time, cello_note)
        bass.insert(current_time, bass_note)
        
        current_time += melody_note.duration.quarterLength
    
    # Add all parts to score
    score.append([violin1, violin2, viola, cello, bass])
    return score

def export_to_musicxml(score, output_path):
    """Export the score as MusicXML."""
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Set part names
        part_names = [
            ("Violin I", "Vln. I"),
            ("Violin II", "Vln. II"),
            ("Viola", "Vla."),
            ("Violoncello", "Vc."),
            ("Contrabass", "Cb.")
        ]
        
        for part, (name, abbrev) in zip(score.parts, part_names):
            part.partName = name
            part.partAbbreviation = abbrev
        
        # Export to MusicXML
        score.write('musicxml', fp=output_path)
    except Exception as e:
        raise Exception(f"Error exporting to MusicXML: {str(e)}")
