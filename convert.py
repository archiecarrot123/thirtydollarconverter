import midi
import instrument_names
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

default_instrument = "noteblock_bass"
default_pitch = 60


# globals
resolution = 0
notes_mixed = []
instruments = []
precussion = False
instrument_widgets = []
instrument_variables = {}
instrument_mappings = {}


root = Tk()
root.title("BEES")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
instframe = ttk.Frame(mainframe, padding="3 3 12 12")
instframe.grid(column=0, row=2, sticky=(N, W, E, S))


class GDCevent:
    def __init__(self, event, value=None):
        self.event = event
        self.value = value
    
    def appendtofile(self, file_, beginning=False):
        suffix = ""
        if self.value:
            suffix = "@" + str(self.value)
        #suffix = "@" + str(self.value)
        if beginning:
            file_.write(self.event + suffix)
        else:
            file_.write("|" + self.event + suffix)

def printdelay(ticks, resolution, bpm):
    if ticks != 0:
        print("delay 1/", round(resolution*bpm/ticks), " minutes", sep="")

def loadmidi(filename):
    global resolution
    pattern = midi.read_midifile(filename)
    print("Format", pattern.format, "MIDI file")
    resolution = pattern.resolution
    print("Resolution:", resolution)
    pattern.make_ticks_abs()
    return pattern

def mix(pattern):
    global precussion
    global instruments
    
    instruments = [] # need to reset instruments
    n = 0
    for track in pattern:
        print("Track", n)
        #print(track)
        mixing_index = 0
        current_instrument = 0
        for event in track:
            if event.statusmsg == 0x90:
                if event.get_velocity() != 0 and event.channel != 9:
                    while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                        mixing_index += 1
                    #print(mixing_index, event.tick, notes_mixed[mixing_index]["tick"], event.tick >= notes_mixed[mixing_index]["tick"])
                    notes_mixed.insert(mixing_index, {'instrument': current_instrument, 'tick': event.tick, 'pitch': event.get_pitch()})
                elif event.channel == 9:
                    precussion = True
            elif event.statusmsg == 0xFF and event.metacommand == 0x51:
                while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                    mixing_index += 1
                #print(mixing_index, event.tick, notes_mixed[mixing_index]["tick"], event.tick >= notes_mixed[mixing_index]["tick"])
                notes_mixed.insert(mixing_index, {'instrument': 'tempo', 'tick': event.tick, 'bpm': event.get_bpm()})
            elif event.statusmsg == 0xC0:
                current_instrument = event.get_value()
                if current_instrument not in instruments:
                    instruments.append(current_instrument)
            else:
                print(event)
        
        n += 1
    
    return notes_mixed

def gdcize(notes):
    gdcevents = []
    delta = 0
    last_tick = 0
    bpm = 120
    freq = 0
    gdcindex = 0
    for note in notes:
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
        gdcevents.append(GDCevent(instrument_mappings[note['instrument']], note['pitch'] - default_pitch))
    return gdcevents
        #print("note", event.get_pitch(), "velocity", event.get_velocity())

def writeevents(gdcevents, filename):
    f = open(filename, 'w')
    for gdcevent in gdcevents:
        gdcevent.appendtofile(f)

def load():
    global notes_mixed
    
    pattern = loadmidi(filedialog.askopenfilename())
    notes_mixed = mix(pattern)
    #print(notes_mixed)
    
    # this should probably be another function but i can't be bothered to make another one
    global instruments
    global instrument_widgets
    global instrument_variables
    global instrument_mappings
    global instframe
    
    # need to clear instrument_widgets each time to avoid issues
    for widgets in instrument_widgets:
        widgets['label'].destroy()
        widgets['combobox'].destroy()
    instrument_widgets = []
    
    n = 0
    for instrument in instruments:
        instrument_variables[instrument] = StringVar(value="noteblock_bass")
        instrument_widgets.append({
            'label': ttk.Label(instframe, text=instrument_names.INSTRUMENT_NAMES[instrument+1]),
            'combobox': ttk.Combobox(instframe, textvariable=instrument_variables[instrument])
            })
        instrument_widgets[n]['label'].grid(column=0, row=n, sticky=(N, W, E, S))
        instrument_widgets[n]['combobox'].grid(column=1, row=n, sticky=(N, W, E, S))
        instrument_widgets[n]['combobox']["values"] = instrument_names.GDC_INSTRUMENTS
        n += 1

def update_instruments():
    global instrument_variables
    global instrument_mappings
    
    for instrument in instrument_variables:
        instrument_mappings[instrument] = instrument_variables[instrument].get()
    print(instrument_mappings)

def run():
    global notes_mixed
    
    update_instruments()
    gdcevents = gdcize(notes_mixed)
    writeevents(gdcevents, filedialog.asksaveasfilename())


openbutton = ttk.Button(mainframe, text="Open", command=load)
openbutton.grid(column=0, row=0, sticky=(N, W, E, S))
runbutton = ttk.Button(mainframe, text="Run", command=run)
runbutton.grid(column=0, row=1, sticky=(N, W, E, S))

root.mainloop()
