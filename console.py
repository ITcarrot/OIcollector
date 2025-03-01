import tkinter as tk
import threading

window = tk.Tk()
window.geometry('800x600')

scrollbar = tk.Scrollbar(window)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_widget = tk.Text(window, bg="black", fg="white",
                      wrap="word", font=('', 15), spacing1=5,
                      yscrollcommand=scrollbar.set)
text_widget.pack(fill=tk.BOTH, expand=True)
text_widget.config(state=tk.DISABLED)
scrollbar.config(command=text_widget.yview)

text_widget.tag_configure("red", foreground="red")
text_widget.tag_configure("yellow", foreground="yellow")
text_widget.tag_configure("green", foreground="green")

space_pressed = threading.Event()
def press_key_space(*args):
    global space_pressed
    space_pressed.set()
window.bind("<KeyPress-space>", press_key_space)

key_pressed = threading.Event()
last_pressed_key = ''
def press_key(event):
    global key_pressed, last_pressed_key
    if not key_pressed.is_set():
        key_pressed.set()
        last_pressed_key = event.char
window.bind('<KeyPress>', press_key)

def start(title: str, main_func: callable):
    window.title(title)
    main_thread = threading.Thread(target=main_func, daemon=True)
    main_thread.start()
    window.mainloop()

def print(text: str, color: str = ''):
    global text_widget
    text_widget.config(state=tk.NORMAL)
    text_widget.insert(tk.END, text, color)
    text_widget.config(state=tk.DISABLED)
    text_widget.yview(tk.END)

def clear():
    global text_widget
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.config(state=tk.DISABLED)

def wait_space():
    global space_pressed
    space_pressed.clear()
    print('请按空格键继续','green')
    print('或关闭窗口退出\n')
    space_pressed.wait()

def get_next_key():
    global key_pressed, last_pressed_key
    key_pressed.clear()
    key_pressed.wait()
    return last_pressed_key
