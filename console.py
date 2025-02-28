import tkinter as tk
import threading

window = tk.Tk()
window.geometry('800x600')

text_widget = tk.Text(window, bg="black", fg="white", wrap="word", font=('', 15), spacing1=5)
text_widget.pack(fill=tk.BOTH, expand=True)
text_widget.config(state=tk.DISABLED)

text_widget.tag_configure("red", foreground="red")
text_widget.tag_configure("yellow", foreground="yellow")
text_widget.tag_configure("green", foreground="green")

y_pressed = threading.Event()
def press_key_y(*args):
    global y_pressed
    y_pressed.set()

window.bind("<KeyPress-y>", press_key_y)
window.bind("<KeyPress-Y>", press_key_y)

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

def wait_y():
    global y_pressed
    y_pressed.clear()
    print('请按y键继续','green')
    print('或关闭窗口退出\n')
    y_pressed.wait()