import midi

instrument = "noteblock_bass"
default_pitch = 60
output_file = "outputfile.🗿"
input_file = "train_filled_with_cash.mid"

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


n = 0
track = pattern[n]
time_signature = [4, 2, 24, 8]
bpm = 120
freq = bpm
gdcevents = []
while True:
    print("Track", n)
    #print(track)
    m = 0
    event = track[m]
    ticks = 0
    gdcindex = 0
    while True:
        ticks += event.tick
        if event.statusmsg == 0x90:
            if event.get_velocity() != 0:
                #printdelay(ticks, resolution, bpm)
                if ticks != 0:
                    if freq != round(resolution*bpm/ticks) and round(resolution*bpm/ticks) != 0:
                        freq = round(resolution*bpm/ticks)
                        gdcevents.insert(gdcindex, GDCevent("!speed", freq))
                        gdcindex += 1
                else:
                    gdcevents.append(GDCevent("!combine"))
                
                gdcevents.append(GDCevent(instrument, event.get_pitch() - default_pitch))
                gdcindex = len(gdcevents) - 1
                ticks = 0
                #print("note", event.get_pitch(), "velocity", event.get_velocity())
        else:
            #printdelay(ticks, resolution, bpm)
            #ticks = 0
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

f = open(output_file, "w")
for gdcevent in gdcevents:
    if gdcevent.event == "!speed":
        gdcevent.appendtofile(f, True)
        break
for gdcevent in gdcevents:
    gdcevent.appendtofile(f)
