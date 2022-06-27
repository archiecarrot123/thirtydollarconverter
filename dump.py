import midi

def printdelay(ticks, resolution, bpm):
    if ticks != 0:
        print("delay 1/", resolution*bpm/ticks, " minutes", sep="")

pattern = midi.read_midifile("example.mid")
print("Format", pattern.format, "MIDI file")
resolution = pattern.resolution
print("Resolution:", resolution)


n = 0
track = pattern[n]
time_signature = [4, 2, 24, 8]
bpm = 120
while True:
    print("Track", n)
    #print(track)
    m = 0
    event = track[m]
    ticks = 0
    while True:
        ticks += event.tick
        if event.statusmsg == 0x90:
            if event.get_velocity() != 0:
                printdelay(ticks, resolution, bpm)
                ticks = 0
                print("note", event.get_pitch(), "velocity", event.get_velocity())
        else:
            printdelay(ticks, resolution, bpm)
            ticks = 0
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
