#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per il login a Garmin Connect
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
from .styles import COLORS

class LoginFrame(ttk.Frame):
    """Frame per il login a Garmin Connect"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con un po' di padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Intestazione
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Connessione a Garmin Connect", 
                 style="Heading.TLabel").pack(side=tk.LEFT)
        
        garmin_logo = ttk.Label(header_frame, text="🔄", font=("Arial", 24))
        garmin_logo.pack(side=tk.RIGHT)
        
        # Frame per il login
        login_frame = ttk.LabelFrame(main_frame, text="Credenziali Garmin Connect")
        login_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=10)
        
        # Griglia per il form di login
        form_frame = ttk.Frame(login_frame, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(form_frame, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=40)
        self.password_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Cartella OAuth
        ttk.Label(form_frame, text="Cartella OAuth:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.oauth_folder_var = tk.StringVar(value=self.controller.config.get('oauth_folder', '~/.garth'))
        self.oauth_folder_entry = ttk.Entry(form_frame, textvariable=self.oauth_folder_var, width=40)
        self.oauth_folder_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Pulsante sfoglia per la cartella OAuth
        self.browse_button = ttk.Button(form_frame, text="Sfoglia...", command=self.browse_oauth_folder)
        self.browse_button.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Salva credenziali
        self.save_creds_var = tk.BooleanVar(value=True)
        self.save_creds_check = ttk.Checkbutton(form_frame, text="Salva token per accessi futuri", 
                                              variable=self.save_creds_var)
        self.save_creds_check.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Frame per i pulsanti
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Pulsante login
        self.login_button = ttk.Button(button_frame, text="Accedi", 
                                     style="Accent.TButton", 
                                     command=self.login)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante logout
        self.logout_button = ttk.Button(button_frame, text="Disconnetti", 
                                      command=self.logout)
        self.logout_button.pack(side=tk.LEFT, padx=5)
        self.logout_button['state'] = 'disabled'
        
        # Frame per lo stato del login
        status_frame = ttk.Frame(form_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E)
        
        # Indicatore di stato
        self.status_var = tk.StringVar(value="In attesa di login")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                    style="Status.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        # Indicatore di progresso
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT)
        
        # Frame informativo
        info_frame = ttk.LabelFrame(main_frame, text="Informazioni sulla connessione")
        info_frame.pack(fill=tk.X, pady=10, padx=50)
        
        info_text = (
            "La connessione a Garmin Connect è necessaria per sincronizzare "
            "gli allenamenti con il tuo account Garmin.\n\n"
            "Le credenziali vengono utilizzate solo per autenticarsi con i server Garmin. "
            "Il token di accesso viene salvato in modo sicuro nella cartella OAuth specificata."
        )
        
        ttk.Label(info_frame, text=info_text, wraplength=500, 
                style="Instructions.TLabel", padding=10).pack(fill=tk.X)
        
    def browse_oauth_folder(self):
        """Apre un selettore di cartelle per la cartella OAuth"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(
            title="Seleziona cartella per il token OAuth",
            initialdir=os.path.expanduser(self.oauth_folder_var.get())
        )
        
        if folder:
            self.oauth_folder_var.set(folder)
            # Aggiorna la configurazione
            self.controller.config['oauth_folder'] = folder
    
    def login(self):
        """Effettua il login a Garmin Connect"""
        # Ottieni i valori
        email = self.email_var.get().strip()
        password = self.password_var.get()
        oauth_folder = os.path.expanduser(self.oauth_folder_var.get())
        
        # Validazione
        if not email:
            messagebox.showerror("Errore", "Inserisci l'indirizzo email", parent=self)
            self.email_entry.focus_set()
            return
        
        if not password:
            messagebox.showerror("Errore", "Inserisci la password", parent=self)
            self.password_entry.focus_set()
            return
        
        # Assicurati che la cartella OAuth esista
        if not os.path.exists(oauth_folder):
            try:
                os.makedirs(oauth_folder)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare la cartella OAuth: {str(e)}", parent=self)
                return
        
        # Disabilita il form durante il login
        self.login_button['state'] = 'disabled'
        self.email_entry['state'] = 'disabled'
        self.password_entry['state'] = 'disabled'
        self.oauth_folder_entry['state'] = 'disabled'
        self.browse_button['state'] = 'disabled'
        self.save_creds_check['state'] = 'disabled'
        
        # Aggiorna lo stato
        self.status_var.set("Login in corso...")
        self.progress.start()
        
        # Effettua il login in un thread separato
        self.login_thread = threading.Thread(target=self._login_thread, 
                                           args=(email, password, oauth_folder))
        self.login_thread.daemon = True
        self.login_thread.start()
    
    def _login_thread(self, email, password, oauth_folder):
        """Thread per il login a Garmin Connect"""
        try:
            # Importa il client Garmin
            from planner.garmin_client import GarminClient
            import garth
            
            # Logga l'inizio del tentativo di login
            logging.info(f"Tentativo di login per l'utente: {email}")
            
            try:
                # Prova a effettuare il login
                garth.login(email, password)
            except Exception as auth_err:
                logging.error(f"Errore di autenticazione: {str(auth_err)}")
                self.controller.after(0, self._login_failed, f"Errore di autenticazione: credenziali non valide o servizio non disponibile. Dettagli: {str(auth_err)}")
                return
            
            # Salva il token se richiesto
            if self.save_creds_var.get():
                try:
                    garth.save(oauth_folder)
                    logging.info(f"Token OAuth salvato in {oauth_folder}")
                except Exception as save_err:
                    logging.warning(f"Impossibile salvare il token OAuth: {str(save_err)}")
                    # Continuiamo comunque con il login
            
            # Crea il client
            try:
                client = GarminClient(oauth_folder)
            except Exception as client_err:
                logging.error(f"Errore nella creazione del client Garmin: {str(client_err)}")
                self.controller.after(0, self._login_failed, f"Errore nella creazione del client Garmin: {str(client_err)}")
                return
            
            # Verifica che il client funzioni
            try:
                _ = client.list_workouts()
                logging.info("Connessione a Garmin Connect verificata con successo")
            except Exception as api_err:
                logging.error(f"Errore nell'accesso alle API di Garmin: {str(api_err)}")
                self.controller.after(0, self._login_failed, f"Errore nell'accesso alle API di Garmin: {str(api_err)}")
                return
            
            # Login riuscito
            logging.info("Login completato con successo")
            self.controller.after(0, self._login_success, client)
            
        except Exception as e:
            # Errore generico
            logging.error(f"Errore imprevisto durante il login: {str(e)}")
            self.controller.after(0, self._login_failed, f"Errore imprevisto: {str(e)}")
    
    def _login_success(self, client):
        """Callback per il login riuscito"""
        # Ferma l'indicatore di progresso
        self.progress.stop()
        
        # Aggiorna lo stato
        self.status_var.set("Login riuscito!")
        
        # Abilita solo il pulsante di logout
        self.login_button['state'] = 'disabled'
        self.logout_button['state'] = 'normal'
        
        # Informa il controller
        self.controller.on_login(client)
    
    def _login_failed(self, error_message):
        """Callback per il login fallito"""
        # Ferma l'indicatore di progresso
        self.progress.stop()
        
        # Aggiorna lo stato
        self.status_var.set("Login fallito!")
        
        # Riabilita il form
        self.login_button['state'] = 'normal'
        self.email_entry['state'] = 'normal'
        self.password_entry['state'] = 'normal'
        self.oauth_folder_entry['state'] = 'normal'
        self.browse_button['state'] = 'normal'
        self.save_creds_check['state'] = 'normal'
        
        # Mostra l'errore
        self.show_login_error(error_message)
    
    def show_login_error(self, error_message):
        """Mostra un messaggio di errore per il login"""
        messagebox.showerror("Errore di login", 
                            f"Impossibile accedere a Garmin Connect: {error_message}", 
                            parent=self)
    
    def logout(self):
        """Effettua il logout da Garmin Connect"""
        if messagebox.askyesno("Conferma logout", 
                             "Sei sicuro di voler effettuare il logout da Garmin Connect?", 
                             parent=self):
            # Cancella il token OAuth
            oauth_folder = os.path.expanduser(self.oauth_folder_var.get())
            try:
                # Cancella solo il file di sessione, non l'intera cartella
                session_file = os.path.join(oauth_folder, 'session.json')
                if os.path.exists(session_file):
                    os.remove(session_file)
            except Exception as e:
                logging.warning(f"Impossibile cancellare la sessione OAuth: {str(e)}")
            
            # Aggiorna lo stato
            self.status_var.set("In attesa di login")
            
            # Riabilita il form
            self.login_button['state'] = 'normal'
            self.logout_button['state'] = 'disabled'
            self.email_entry['state'] = 'normal'
            self.password_entry['state'] = 'normal'
            self.oauth_folder_entry['state'] = 'normal'
            self.browse_button['state'] = 'normal'
            self.save_creds_check['state'] = 'normal'
            
            # Cancella la password (ma non l'email)
            self.password_var.set("")
            
            # Informa il controller
            self.controller.on_logout()
    
    def update_ui_after_login(self):
        """Aggiorna l'interfaccia dopo un login automatico"""
        # Aggiorna lo stato
        self.status_var.set("Login riuscito!")
        
        # Abilita solo il pulsante di logout
        self.login_button['state'] = 'disabled'
        self.logout_button['state'] = 'normal'
        
        # Disabilita il form
        self.email_entry['state'] = 'disabled'
        self.password_entry['state'] = 'disabled'
        self.oauth_folder_entry['state'] = 'disabled'
        self.browse_button['state'] = 'disabled'
        self.save_creds_check['state'] = 'disabled'