import tkinter as tk
from tkinter import ttk
import threading
import sys

class LoadingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Lancement de l'application")
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        
        # Centrer la fenêtre
        self.root.eval('tk::PlaceWindow . center')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principale
        frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title = tk.Label(frame, text="🚀 Gestion de Comptes", 
                        font=('Segoe UI', 14, 'bold'), bg='white', fg='#2c3e50')
        title.pack(pady=(0, 10))
        
        # Message de statut
        self.status_label = tk.Label(frame, text="Initialisation...", 
                                     font=('Segoe UI', 10), bg='white', fg='#7f8c8d')
        self.status_label.pack(pady=(0, 10))
        
        # Barre de progression
        self.progress = ttk.Progressbar(frame, mode='indeterminate', length=350)
        self.progress.pack(pady=10)
        self.progress.start(10)
        
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()
    
    def close(self):
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    window = LoadingWindow()
    if len(sys.argv) > 1:
        window.update_status(sys.argv[1])
    window.run()
