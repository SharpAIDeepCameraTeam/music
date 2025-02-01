import os
import music21
import random
import note_seq
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.protobuf import generator_pb2
from magenta.music import sequence_generator_bundle
from magenta.music.protobuf import music_pb2

def create_sequence_from_scratch(key='C', time_signature='4/4', tempo=120):
    """Create a new sequence in ABA form with sophisticated string writing."""
    score = music21.stream.Score()
    
    # Create metadata
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "String Orchestra in ABA Form"
    
    # Create a part for the melody
    melody_part = music21.stream.Part()
    
    # Add key signature and tempo
    key_obj = music21.key.Key(key)
    melody_part.append(key_obj)
    melody_part.append(music21.meter.TimeSignature(time_signature))
    melody_part.append(music21.tempo.MetronomeMark(number=tempo))
    
    # Get scale for the key
    scale = key_obj.getScale()
    scale_pitches = [p.midi for p in scale.getPitches()]
    
    # More sophisticated rhythmic patterns
    rhythms = {
        'main_theme': [  # For A sections
            [2.0, 1.0, 1.0],  # Long-short-short
            [1.5, 0.5, 1.0, 1.0],  # Dotted rhythm
            [1.0, 1.0, 2.0],  # Build to long note
        ],
        'contrasting': [  # For B section
            [0.5, 0.5, 0.5, 0.5, 2.0],  # Faster movement to long
            [0.25, 0.25, 0.5, 0.5, 1.0, 1.5],  # More complex
            [1.0, 0.5, 0.5, 1.0, 1.0]  # Mixed rhythms
        ]
    }
    
    def create_phrase(section_type, length=4):
        """Create a musical phrase with specific character."""
        phrase = []
        
        current_measure = music21.stream.Measure()
        remaining_length = length * 4.0  # measures * beats per measure
        
        # Choose primary scale degrees for each section
        if section_type == 'A':
            primary_degrees = [0, 2, 4, 7]  # Strong, stable degrees
        else:  # B section
            primary_degrees = [1, 3, 5, 6]  # More tension, movement
        
        while remaining_length > 0:
            # Choose rhythm pattern based on section
            pattern = random.choice(rhythms['main_theme' if section_type == 'A' else 'contrasting'])
            
            for rhythm in pattern:
                if rhythm <= remaining_length:
                    # Create more purposeful melody
                    if random.random() < 0.7:  # 70% chance of primary degrees
                        pitch_idx = random.choice([p for i, p in enumerate(scale_pitches) if i % 7 in primary_degrees])
                    else:  # 30% chance of other scale degrees
                        pitch_idx = random.choice(scale_pitches)
                    
                    note = music21.note.Note(pitch_idx, quarterLength=rhythm)
                    
                    # Add dynamics and articulations
                    if section_type == 'A':
                        if rhythm >= 2.0:  # Long notes
                            note.expressions.append(music21.expressions.Crescendo())
                        elif random.random() < 0.3:
                            note.articulations.append(music21.articulations.Accent())
                    else:  # B section
                        if rhythm <= 0.5:  # Short notes
                            note.articulations.append(music21.articulations.Staccato())
                        elif random.random() < 0.4:
                            note.expressions.append(music21.expressions.Diminuendo())
                    
                    current_measure.append(note)
                    remaining_length -= rhythm
                    
                    # Start new measure if current is full
                    if current_measure.duration.quarterLength >= 4.0:
                        phrase.append(current_measure)
                        current_measure = music21.stream.Measure()
        
        if current_measure.duration.quarterLength > 0:
            phrase.append(current_measure)
        return phrase
    
    # Create ABA form with Magenta-enhanced B section
    section_A = create_phrase('A', 8)  # 8 measures for A
    
    # Use Magenta to generate contrasting B section
    try:
        # Convert A section to NoteSequence for reference
        sequence = music_pb2.NoteSequence()
        time = 0
        for measure in section_A:
            for note in measure.notes:
                sequence.notes.add(
                    pitch=note.pitch.midi,
                    start_time=time,
                    end_time=time + note.duration.quarterLength,
                    velocity=80
                )
                time += note.duration.quarterLength
        sequence.total_time = time
        
        # Initialize Magenta generator
        bundle = sequence_generator_bundle.read_bundle_file('basic_rnn.mag')
        generator_map = melody_rnn_sequence_generator.get_generator_map()
        generator = generator_map['basic_rnn'](checkpoint=None, bundle=bundle)
        
        # Generate B section
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = 1.2  # More variation for B section
        generator_options.generate_sections.add(
            start_time=0,
            end_time=32.0  # 8 measures
        )
        
        b_sequence = generator.generate(sequence, generator_options)
        
        # Convert back to Music21
        section_B = []
        current_measure = music21.stream.Measure()
        current_time = 0
        
        for note in b_sequence.notes:
            duration = note.end_time - note.start_time
            n = music21.note.Note(note.pitch, quarterLength=duration)
            
            # Add B section characteristics
            if duration <= 0.5:
                n.articulations.append(music21.articulations.Staccato())
            elif random.random() < 0.4:
                n.expressions.append(music21.expressions.Diminuendo())
            
            current_measure.append(n)
            current_time += duration
            
            if current_measure.duration.quarterLength >= 4.0:
                section_B.append(current_measure)
                current_measure = music21.stream.Measure()
        
        if current_measure.duration.quarterLength > 0:
            section_B.append(current_measure)
            
    except Exception as e:
        print(f"Magenta generation failed: {str(e)}, falling back to basic B section")
        section_B = create_phrase('B', 8)
    
    # Create final A section with slight variations
    section_A2 = create_phrase('A', 8)
    
    # Add all sections to the melody part
    for section in [section_A, section_B, section_A2]:
        for measure in section:
            melody_part.append(measure)
    
    score.append(melody_part)
    return score

def parse_input_file(file_path):
    """Parse input MIDI or MusicXML file."""
    try:
        return music21.converter.parse(file_path)
    except Exception as e:
        raise Exception(f"Error parsing input file: {str(e)}")

def generate_music(input_sequence=None, key='C', time_signature='4/4', 
                  tempo=120, temperature=1.0):
    """Generate music using Magenta and Music21."""
    try:
        if input_sequence is None:
            return create_sequence_from_scratch(key, time_signature, tempo)

        # Convert Music21 sequence to NoteSequence
        sequence = music_pb2.NoteSequence()
        time = 0
        for note in input_sequence.flat.notes:
            if note.isNote:
                sequence.notes.add(
                    pitch=note.pitch.midi,
                    start_time=time,
                    end_time=time + note.duration.quarterLength,
                    velocity=note.volume.velocity if note.volume.velocity else 80
                )
                time += note.duration.quarterLength
        sequence.total_time = time
        
        # Initialize Magenta generator
        bundle = sequence_generator_bundle.read_bundle_file('basic_rnn.mag')
        generator_map = melody_rnn_sequence_generator.get_generator_map()
        generator = generator_map['basic_rnn'](checkpoint=None, bundle=bundle)
        
        # Generate continuation
        generator_options = generator_pb2.GeneratorOptions()
        generator_options.args['temperature'].float_value = temperature
        generator_options.generate_sections.add(
            start_time=sequence.total_time,
            end_time=sequence.total_time + 32.0  # Generate 8 measures
        )
        
        generated_sequence = generator.generate(sequence, generator_options)
        
        # Convert back to Music21
        score = music21.stream.Score()
        part = music21.stream.Part()
        
        for note in generated_sequence.notes:
            n = music21.note.Note(
                pitch=note.pitch,
                quarterLength=note.end_time - note.start_time
            )
            n.offset = note.start_time
            part.insert(n.offset, n)
        
        score.append(part)
        return score
            
    except Exception as e:
        print(f"Generation error: {str(e)}")
        # Fallback to original melody generation if Magenta fails
        return create_sequence_from_scratch(key, time_signature, tempo)

def harmonize_for_strings(score):
    """Create a string orchestra arrangement from the score with proper voice leading."""
    try:
        full_score = music21.stream.Score()
        
        # Copy over key and tempo from original score
        key_context = None
        for element in score.flat:
            if isinstance(element, music21.key.Key):
                key_context = element
                full_score.append(element)
            elif isinstance(element, music21.tempo.MetronomeMark):
                full_score.append(element)
        
        if not key_context:
            key_context = music21.key.Key('C')
            full_score.append(key_context)
        
        # Create parts
        violin1 = score.parts[0].flat  # Flatten the part for faster processing
        violin2 = music21.stream.Part()
        viola = music21.stream.Part()
        cello = music21.stream.Part()
        bass = music21.stream.Part()
        
        # Set instruments
        violin2.append(music21.instrument.Violin())
        viola.append(music21.instrument.Viola())
        cello.append(music21.instrument.Violoncello())
        bass.append(music21.instrument.Contrabass())
        
        # Get scale degrees map for the key
        scale = key_context.getScale()
        scale_degrees = {p.name: i + 1 for i, p in enumerate(scale.pitches)}
        
        # Previous notes for voice leading
        prev_notes = {
            'violin2': None,
            'viola': None,
            'cello': None,
            'bass': None
        }
        
        # Process each note in the melody
        for note in violin1.notes:
            if isinstance(note, music21.note.Note):
                # Get scale degree of the current note
                scale_degree = scale_degrees.get(note.pitch.name, 1)
                
                # Determine chord based on scale degree
                if scale_degree in [1, 4, 5]:  # Strong scale degrees
                    chord_intervals = [0, 4, 7]  # Root position triad
                elif scale_degree in [2, 3, 6]:  # Weaker scale degrees
                    chord_intervals = [0, 3, 7]  # Minor triad
                else:  # Diminished for 7th scale degree
                    chord_intervals = [0, 3, 6]
                
                # Create harmony notes with voice leading
                v2_note = create_harmony_note(note, chord_intervals[0], prev_notes['violin2'], 55, 88)  # G3 to E6
                viola_note = create_harmony_note(note, chord_intervals[1], prev_notes['viola'], 48, 79)  # C3 to G5
                cello_note = create_harmony_note(note, chord_intervals[2], prev_notes['cello'], 36, 72)  # C2 to C5
                bass_note = create_harmony_note(note, 0, prev_notes['bass'], 28, 60)  # E1 to C4
                
                # Update previous notes
                prev_notes['violin2'] = v2_note
                prev_notes['viola'] = viola_note
                prev_notes['cello'] = cello_note
                prev_notes['bass'] = bass_note
                
                # Add notes to parts
                violin2.insert(note.offset, v2_note)
                viola.insert(note.offset, viola_note)
                cello.insert(note.offset, cello_note)
                bass.insert(note.offset, bass_note)
            else:
                # Copy rests to all parts
                for part in [violin2, viola, cello, bass]:
                    part.insert(note.offset, note)
        
        # Add all parts to score
        full_score.append([violin1.getElementsNotOfClass('Instrument'), violin2, viola, cello, bass])
        return full_score
        
    except Exception as e:
        raise Exception(f"Error harmonizing: {str(e)}")

def create_harmony_note(melody_note, interval, prev_note, min_pitch, max_pitch):
    """Create a harmony note with proper voice leading."""
    # Start with the basic interval
    new_note = melody_note.transpose(interval)
    
    # Ensure note is within the instrument's range
    while new_note.pitch.midi < min_pitch:
        new_note = new_note.transpose(12)
    while new_note.pitch.midi > max_pitch:
        new_note = new_note.transpose(-12)
    
    # Apply voice leading if there's a previous note
    if prev_note:
        # Try to minimize movement between notes
        interval_to_prev = abs(new_note.pitch.midi - prev_note.pitch.midi)
        if interval_to_prev > 7:  # If interval is larger than a fifth
            # Try the note an octave in the opposite direction
            alternative = new_note.transpose(12 if new_note.pitch.midi < prev_note.pitch.midi else -12)
            if min_pitch <= alternative.pitch.midi <= max_pitch:
                new_alternative_interval = abs(alternative.pitch.midi - prev_note.pitch.midi)
                if new_alternative_interval < interval_to_prev:
                    new_note = alternative
    
    return new_note.transpose(0)  # Return a copy

def export_to_musicxml(score, output_path):
    """Export the score as MusicXML with proper part names and instrument assignments."""
    try:
        # Set part names and abbreviations
        part_info = {
            0: ("Violin I", "Vln. I"),
            1: ("Violin II", "Vln. II"),
            2: ("Viola", "Vla."),
            3: ("Violoncello", "Vc."),
            4: ("Contrabass", "Cb.")
        }
        
        for i, part in enumerate(score.parts):
            if i in part_info:
                part.partName = part_info[i][0]
                part.partAbbreviation = part_info[i][1]
        
        # Add title and composer if not present
        if not score.metadata:
            score.metadata = music21.metadata.Metadata()
            score.metadata.title = "String Orchestra Arrangement"
            score.metadata.composer = "Generated by SoundWave Studios"
        
        # Export to MusicXML
        score.write('musicxml', output_path)
    except Exception as e:
        raise Exception(f"Error exporting to MusicXML: {str(e)}")
