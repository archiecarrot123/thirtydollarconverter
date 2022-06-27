import midi

instrument = "noteblock_bass"
default_pitch = 60
output_file = "outputfile.🗿"
input_file = "train_filled_with_cash.mid"
#input_file = "example.mid"


def printdelay(ticks, resolution, bpm):
    if ticks != 0:
        print("delay 1/", round(resolution*bpm/ticks), " minutes", sep="")
        
class GDCevent:
    def __init__(self, event, value=None):
        self.event = event
        self.value = value
    
    def appendtofile(self, file_, beginning=False):
        suffix = ""
        if self.value:
            suffix = "@" + str(self.value)
        if beginning:
            file_.write(self.event + suffix)
        else:
            file_.write("|" + self.event + suffix)

pattern = midi.read_midifile(input_file)
print("Format", pattern.format, "MIDI file")
resolution = pattern.resolution
print("Resolution:", resolution)
pattern.make_ticks_abs()


n = 0
track = pattern[n]
notes_mixed = [{'instrument': 'dummy', 'tick': 0}]
while True:
    print("Track", n)
    #print(track)
    m = 0
    event = track[m]
    mixing_index = 0
    while True:
        if event.statusmsg == 0x90:
            if event.get_velocity() != 0:
                while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                    mixing_index += 1
                #print(mixing_index, event.tick, notes_mixed[mixing_index]["tick"], event.tick >= notes_mixed[mixing_index]["tick"])
                notes_mixed.insert(mixing_index, {'instrument': instrument, 'tick': event.tick, 'pitch': event.get_pitch()})
        elif event.statusmsg == 0xFF and event.metacommand == 0x51:
                while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                    mixing_index += 1
                #print(mixing_index, event.tick, notes_mixed[mixing_index]["tick"], event.tick >= notes_mixed[mixing_index]["tick"])
                notes_mixed.insert(mixing_index, {'instrument': 'tempo', 'tick': event.tick, 'bpm': event.get_bpm()})
        else:
            print(event)
        m += 1
        try:
            event = track[m]
        except IndexError:
            break
    
    n += 1
    if pattern.format == 0:
        break
    try:
        track = pattern[n]
    except IndexError:
        break
#print(notes_mixed)


gdcevents = []
delta = 0
last_tick = 0
time_signature = [4, 2, 24, 8]
bpm = 120
freq = 0
gdcindex = 0
for note in notes_mixed:
    if note['instrument'] == 'dummy':
        continue
    if note['instrument'] == 'tempo':
        bpm = note['bpm']
        continue
    
    delta = note['tick'] - last_tick
    #print(note['tick'], last_tick, delta)
    last_tick = note['tick']
    if delta != 0:
        if freq != round(resolution*bpm/delta) and round(resolution*bpm/delta) != 0:
            freq = round(resolution*bpm/delta)
            gdcevents.insert(gdcindex, GDCevent("!speed", freq))
            gdcindex += 1
    else:
        gdcevents.append(GDCevent("!combine"))
    
    gdcindex = len(gdcevents)
    gdcevents.append(GDCevent(note['instrument'], note['pitch'] - default_pitch))
    #print("note", event.get_pitch(), "velocity", event.get_velocity())


f = open(output_file, "w")
for gdcevent in gdcevents:
    if gdcevent.event == "!speed":
        gdcevent.appendtofile(f, True)
        break
for gdcevent in gdcevents:
    gdcevent.appendtofile(f)
