import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import scipy.io as sio
import struct
import time
import serial
from tkinter import simpledialog
from tkinter import messagebox
import re

# Window
window = tk.Tk()
window.title("Interface")

file = ["","",""]
data = [0,0,0]
dataC = [0,0,0]
correction_factor = 0
difference = [0,0]
mean_time_sum_alt = [0,0]
mean_time_sum_var = [tk.StringVar(),tk.StringVar(),tk.StringVar()]
jitter = [tk.StringVar(),tk.StringVar(),tk.StringVar()]


def load_matrix(index):
    global data
    global file
    
    data1 = sio.loadmat(file[index])
    if file[0] == "":
        messagebox.showinfo("Information","You should first load the noise matrix")
        return
    else:
        data[index] = data1["data1"][:,237:657]
        data_corrected(index)
    
    
    
def calculate_correction_factor(index):
    global data
    global correction_factor
    histSum = np.sum(data[index], axis=0)
    histMean = np.mean(histSum)
    DNL = (histSum/histMean)-1
    correction_factor = 1/(1 + DNL)
    
      
def data_corrected(index):
    global data
    global correction_factor
    global dataC
    calculate_correction_factor(0)
    data2 = data[index] * correction_factor
    dataC[index] = np.sum(data2,axis=0)
    
    
def mean_time_ind(index):
    global data
    global correction_factor
    global difference
    global jitter
    global file
    
    if index == 1 and file[1] == "":
        messagebox.showerror("Error Jitter IRF","You should load the IRF before calculating the jitter")
        return
    elif index == 2 and file[2] == "":
        messagebox.showerror("Error Jitter TPSF","You should load the TPSF before calculating the jitter")
        return
    elif file[0] == "":
        messagebox.showinfo("Information","You should first load the noise matrix before calculating the jitter")
        return
    else:
        mean_t_ind = np.zeros(20)
        for i in range(0,20):
            data_i = data[index][i,:]*correction_factor
            if index == 1:
                mean_t_ind[i] = np.sum(data_i[228:246]*np.arange(228,246))/np.sum(data_i[228:246])
            else:
                mean_t_ind[i] = np.sum(data_i[233:343]*np.arange(233,343))/np.sum(data_i[233:343])
        
        if index == 1:
            maximum = np.max(mean_t_ind)
            minimum = np.min(mean_t_ind)
            difference[0] = (maximum - minimum)*59.8
            jitter[1].set("Jitter: {}".format(difference[0]))
        else:
            maximum = np.max(mean_t_ind)
            minimum = np.min(mean_t_ind)
            difference[1] = (maximum - minimum)*59.8
            jitter[2].set("Jitter: {}".format(difference[1]))
        
                
    
def mean_time_sum(index):
    global data
    global dataC
    global mean_time_sum_var
    global mean_time_sum_alt
    global file
    
    if index == 1 and file[1] == "":
        messagebox.showerror("Error Average Time IRF","You should load the IRF before calculating the average time")
        return
    elif index == 2 and file[2] == "":
        messagebox.showerror("Error Average Time TPSF","You should load the TPSF before calculating the average time")
        return
    elif file[0] == "":
        messagebox.showinfo("Information","You should first load the noise matrix before calculating the average time")
        return
    else:
        if index == 1:
            mean_time_sum_alt[0] = ((np.sum(dataC[index][228:246]*np.arange(228,246))/np.sum(dataC[index][228:246]))+237)*59.8 #Esto último es para ajustar los valores al plot
            mean_time_sum_var[1].set("Average time: {}".format(mean_time_sum_alt[0]))
        else: 
            mean_time_sum_alt[1] = ((np.sum(dataC[index][233:343]*np.arange(233,343))/np.sum(dataC[index][233:343]))+237)*59.8 #Esto último es para ajustar los valores al plot
            mean_time_sum_var[2].set("Average time: {}".format(mean_time_sum_alt[1]))
    
            
def draw_function(index):
    global file
    global ax
    global data
    global canvas
    global dataC
    
    if file[0] == "":
        messagebox.showinfo("Information","You should first load the noise matrix")
        return
    elif index == 1 and file[1] == "":
        messagebox.showwarning("Warning IRF","You should load the IRF before plotting it")
        return
    elif index == 2 and file[2] == "":
        messagebox.showwarning("Warning TPSF","You should load the TPSF before plotting it")
        return
    else:
        #data_corrected(index)
        ax[index].clear
        ax[index].plot(np.arange(237*59.8,657*59.8,59.8),dataC[index])
        canvas[index].draw()
    

def open_file(index):
    global file;
    
    file[index] = tk.filedialog.askopenfilename(title = "Open file") 
    if file[index] == "":
        messagebox.showwarning("Warning file","No file selected")
        return
    elif (re.search('noise', file[index]) and index == 0) is False:
        messagebox.showwarning("Warning noise plot","Plot the noise function in the corresponding window")
        return
    elif (re.search('irf', file[index]) and index == 1) is False:
        messagebox.showwarning("Warning IRF plot","Plot the IRF in the corresponding window")
        return
    elif (re.search('r\d_p\d', file[index]) and index == 2) is False:
        messagebox.showwarning("Warning TPSF plot","Plot the TPSF in the corresponding window")
        return
    else: 
        load_matrix(index)


def readFromArduino():
    
    fileName = simpledialog.askstring("Input", "Introduce the filename (file.mat)",
                                parent=window)
    if fileName is not None:
        print("Filename: ", fileName)
    else:
        messagebox.showwarning("Warning filename","No filename introduced")
        return
    
    string_num_steps = simpledialog.askstring("Input", "How many steps do you want to perform?",
                                parent=window)
    
    if string_num_steps is not None:
        print("num_steps: ", string_num_steps)
        num_steps = int(string_num_steps)
    else:
        messagebox.showwarning("Warning steps","No steps introduced")
        return
        
        
    s = serial.Serial('COM3', 9600, timeout=10)   
    time.sleep(5)
    numBytes_base = 768
    bytesFactor = 2
    numBytes_single = numBytes_base*bytesFactor
    numBytes = numBytes_single
        
    countrate_1 = []
    
    data_total_1 = []
    
    for kk in range(num_steps):
        print(kk)
        dataInt_1 = []; dataInt_2 = [];
        
        s.write(bytes(" ","ascii")); dataSerial = s.read(numBytes)
        dataSerial_1 = dataSerial[0:numBytes_single]
        
        tR_1 = dataSerial_1
        
        dataIndividual_1 = []
        for ii in range(numBytes_base):
            dataIndividual_1.append(bytes('\x00\x00',"ascii")+tR_1[bytesFactor*ii:bytesFactor*(ii+1)])
        try:
            a =  list(map(lambda x:struct.unpack('>I', x)[0], dataIndividual_1) )
            dataInt_1.append(a)
        except:
            dataInt_1.append([0]*numBytes_base)
        
        data_total_1.append(dataInt_1);

        time.sleep(0)
            
    countrate_1.append( np.sum(data_total_1) )
    print("Average Countrate: {}".format(np.sum(data_total_1)/num_steps))

    s.close()
    
    sio.savemat(fileName, mdict=dict(data1=np.squeeze(np.array(data_total_1)),countrate1=countrate_1))


# Configure graphs
fig1, ax1 = plt.subplots(1,1)
fig2, ax2 = plt.subplots(1,1)
fig3, ax3 = plt.subplots(1,1)


#Noise
ax1.set_xlim(237*59.8, 657*59.8)
ax1.set_ylim(0, 400)
ax1.axhline(0, color='black', linewidth=1)
ax1.axvline(0, color='black', linewidth=1)
ax1.set_title("Noise")
canvas1 = FigureCanvasTkAgg(fig1)
canvas1.get_tk_widget().grid(row=0, column=0)

#IRF
ax2.set_xlim(237*59.8, 657*59.8)
ax2.set_ylim(0, 17500)
ax2.axhline(0, color='black', linewidth=1)
ax2.axvline(0, color='black', linewidth=1)
ax2.set_title("IRF")
canvas2 = FigureCanvasTkAgg(fig2)
canvas2.get_tk_widget().grid(row=0, column=1)

#sumTPSF
ax3.set_xlim(237*59.8, 657*59.8)
ax3.set_ylim(0, 3700)
ax3.axhline(0, color='black', linewidth=1)
ax3.axvline(0, color='black', linewidth=1)
ax3.set_title("TPSF sum")
canvas3 = FigureCanvasTkAgg(fig3)
canvas3.get_tk_widget().grid(row=0, column=2)

ax = [ax1,ax2,ax3]
canvas = [canvas1,canvas2,canvas3]

# Buttons
draw_button_noise = tk.Button(window, text="Plot noise function", command=lambda: draw_function(0))
draw_button_noise.grid(row=3, column=0)
load_button_noise = tk.Button(window, text= "Load file", command =lambda: open_file(0))
load_button_noise.grid(row=2, column=0)

draw_button_IRF = tk.Button(window, text="Plot IRF", command=lambda: draw_function(1))
draw_button_IRF.grid(row=4, column=1)
load_button_IRF = tk.Button(window, text= "Load file", command =lambda: open_file(1))
load_button_IRF.grid(row=3, column=1)

draw_button_TPSF = tk.Button(window, text="Plot TPSF", command=lambda: draw_function(2))
draw_button_TPSF.grid(row=4, column=2)
load_button_TPSF = tk.Button(window, text= "Load file", command = lambda: open_file(2))
load_button_TPSF.grid(row=3, column=2)

individualTimeIRF_button = tk.Button(window, text= "Jitter", command =lambda: mean_time_ind(1))
individualTimeIRF_button.grid(row=6, column=1)
sumTimeIRF_button = tk.Button(window, text= "Average time", command =lambda: mean_time_sum(1))
sumTimeIRF_button.grid(row=5, column=1)

individualTimeTPSF_button = tk.Button(window, text= "Jitter", command =lambda: mean_time_ind(2))
individualTimeTPSF_button.grid(row=6, column=2)
sumTimeTPSF_button = tk.Button(window, text= "Average time", command =lambda: mean_time_sum(2))
sumTimeTPSF_button.grid(row=5, column=2)

save_Arduino_button = tk.Button(window, text = "Read and save data from Arduino", command =lambda: readFromArduino())
save_Arduino_button.grid(row=6, column= 0)


#Label Mean time
Average_label_IRF = tk.Label(window,text="", textvariable=mean_time_sum_var[1])
Average_label_IRF.grid(row=1, column=1)

Jitter_label_IRF = tk.Label(window,text="", textvariable=jitter[1])
Jitter_label_IRF.grid(row=2, column=1)

Average_label_TPSF = tk.Label(window,text="", textvariable=mean_time_sum_var[2])
Average_label_TPSF.grid(row=1, column=2)

Jitter_label_TPSF = tk.Label(window,text="", textvariable=jitter[2])
Jitter_label_TPSF.grid(row=2, column=2)


window.mainloop()





