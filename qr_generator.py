import qrcode
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
import json
import os
from datetime import datetime
import webbrowser
import csv
import zipfile
import tempfile
import shutil
from pathlib import Path
import threading
import time
import cv2
import numpy as np
from io import BytesIO
import base64
import requests
import svgwrite
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode.image.svg


class ModernQRGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("harzad qr generator")
        self.root.geometry("1200x900")

        # Initialize style first
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Theme and appearance
        self.dark_mode = tk.BooleanVar(value=False)
        self.current_theme = "light"
        self.theme_colors = {
            "light": {"bg": "#f0f2f5", "card": "#ffffff", "text": "#2c3e50", "accent": "#3498db"},
            "dark": {"bg": "#1a1a1a", "card": "#2d2d2d", "text": "#ecf0f1", "accent": "#2980b9"}
        }

        # Advanced QR settings
        self.fill_color = tk.StringVar(value="#000000")
        self.bg_color = tk.StringVar(value="#FFFFFF")
        self.logo_path = tk.StringVar()
        self.qr_size = tk.IntVar(value=300)
        self.border_size = tk.IntVar(value=4)
        self.error_correction = tk.StringVar(value="H (High)")
        self.wifi_security = tk.StringVar(value="WPA")
        self.qr_shape = tk.StringVar(value="squares")
        self.gradient_start = tk.StringVar(value="#000000")
        self.gradient_end = tk.StringVar(value="#000000")
        self.use_gradient = tk.BooleanVar(value=False)
        self.transparent_bg = tk.BooleanVar(value=False)

        # Data type tracking
        self.current_data_type = tk.StringVar(value="text")

        # History and preferences
        self.history_data = []
        self.user_preferences = {}

        # Camera and scanning
        self.camera_active = False
        self.cap = None

        self.setup_ui()
        self.load_history()
        self.load_preferences()
        self.apply_theme()

    def configure_styles(self):
        """Configure modern styles for widgets"""
        theme = self.theme_colors[self.current_theme]

        self.style.configure('Title.TLabel',
                             font=('Segoe UI', 24, 'bold'),
                             background=theme['bg'],
                             foreground=theme['text'])

        self.style.configure('Card.TFrame',
                             background=theme['card'],
                             relief='raised',
                             borderwidth=1)

        self.style.configure('Primary.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             background=theme['accent'],
                             foreground='white',
                             focuscolor='none')

        self.style.configure('Success.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             background='#27ae60',
                             foreground='white')

        self.style.configure('Accent.TButton',
                             font=('Segoe UI', 10),
                             background='#95a5a6',
                             foreground='white')

        self.style.configure('Modern.TEntry',
                             fieldbackground='white',
                             borderwidth=2,
                             relief='solid')

    def setup_ui(self):
        """Setup the modern user interface with sidebar navigation"""
        # Header with theme toggle
        header_frame = ttk.Frame(self.root, style='Card.TFrame')
        header_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(header_frame, text="HARZAD QR generator pro",
                  style='Title.TLabel').pack(side='left', pady=15)

        # Theme toggle
        ttk.Checkbutton(header_frame, text="Dark Mode",
                        variable=self.dark_mode,
                        command=self.toggle_theme).pack(side='right', padx=10)

        # Main container with sidebar and content
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Sidebar navigation
        self.setup_sidebar(main_container)

        # Content area
        self.content_frame = ttk.Frame(main_container, style='Card.TFrame')
        self.content_frame.pack(side='right', fill='both',
                                expand=True, padx=(10, 0))

        # Initialize with standard QR tab
        self.show_standard_tab()

    def setup_sidebar(self, parent):
        """Setup sidebar navigation"""
        sidebar = ttk.Frame(parent, style='Card.TFrame', width=200)
        sidebar.pack(side='left', fill='y', padx=(0, 10))
        sidebar.pack_propagate(False)

        nav_items = [
            ("📱 Standard QR", self.show_standard_tab),
            ("🔍 QR Scanner", self.show_scanner_tab),
            ("📊 Data Types", self.show_datatype_tab),
            ("🚀 Bulk Generate", self.show_bulk_tab),
            ("🏢 Business", self.show_business_tab),
            ("🔒 Security", self.show_security_tab),
            ("⚡ Smart Features", self.show_smart_tab),
            ("🎨 Creative", self.show_creative_tab),
            ("📚 History", self.show_history_tab),
            ("⚙️ Settings", self.show_settings_tab)
        ]

        for text, command in nav_items:
            btn = ttk.Button(sidebar, text=text,
                             command=command, style='Accent.TButton')
            btn.pack(fill='x', padx=10, pady=5)

    def show_standard_tab(self):
        """Show standard QR code generation tab"""
        self.clear_content()

        # Real-time preview section
        preview_frame = ttk.LabelFrame(
            self.content_frame, text="Real-time Preview", padding=15)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Input and preview side by side
        input_preview_container = ttk.Frame(preview_frame)
        input_preview_container.pack(fill='both', expand=True)

        # Input section
        input_frame = ttk.Frame(input_preview_container)
        input_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        ttk.Label(input_frame, text="Enter text or URL:").pack(
            anchor='w', pady=5)
        self.entry_data = scrolledtext.ScrolledText(
            input_frame, height=4, width=40)
        self.entry_data.pack(fill='both', expand=True, pady=5)
        self.entry_data.bind('<KeyRelease>', self.update_real_time_preview)

        # Data type detection
        type_frame = ttk.Frame(input_frame)
        type_frame.pack(fill='x', pady=5)
        ttk.Label(type_frame, text="Detected Type:").pack(side='left')
        self.data_type_label = ttk.Label(
            type_frame, text="Text", foreground="green")
        self.data_type_label.pack(side='left', padx=5)

        # Preview section
        preview_container = ttk.Frame(input_preview_container)
        preview_container.pack(side='right', fill='both', padx=(10, 0))

        self.preview_label = ttk.Label(preview_container, text="Preview will appear here",
                                       background='white', relief='solid', borderwidth=1)
        self.preview_label.pack(pady=10, ipadx=80, ipady=80)

        # Advanced customization section
        self.setup_advanced_customization(preview_frame)

        # Generate button
        ttk.Button(preview_frame, text="Generate QR Code",
                   command=self.generate_qr, style='Success.TButton').pack(pady=15)

    def setup_advanced_customization(self, parent):
        """Setup advanced QR customization options"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='x', pady=10)

        # Colors tab
        colors_tab = ttk.Frame(notebook)
        notebook.add(colors_tab, text="Colors & Styles")

        # Basic colors
        color_frame = ttk.Frame(colors_tab)
        color_frame.pack(fill='x', pady=5)

        ttk.Button(color_frame, text="Fill Color",
                   command=self.choose_fill_color, style='Accent.TButton').pack(side='left', padx=5)
        self.fill_color_label = ttk.Label(
            color_frame, text="■", foreground=self.fill_color.get(), font=('Arial', 14))
        self.fill_color_label.pack(side='left', padx=5)

        ttk.Button(color_frame, text="Background Color",
                   command=self.choose_bg_color, style='Accent.TButton').pack(side='left', padx=5)
        self.bg_color_label = ttk.Label(
            color_frame, text="■", foreground=self.bg_color.get(), font=('Arial', 14))
        self.bg_color_label.pack(side='left', padx=5)

        # Gradient options
        gradient_frame = ttk.Frame(colors_tab)
        gradient_frame.pack(fill='x', pady=5)

        ttk.Checkbutton(gradient_frame, text="Use Gradient Fill",
                        variable=self.use_gradient,
                        command=self.update_real_time_preview).pack(side='left', padx=5)

        ttk.Button(gradient_frame, text="Start Color",
                   command=lambda: self.choose_gradient_color('start')).pack(side='left', padx=5)
        ttk.Button(gradient_frame, text="End Color",
                   command=lambda: self.choose_gradient_color('end')).pack(side='left', padx=5)

        # Shape selection
        shape_frame = ttk.Frame(colors_tab)
        shape_frame.pack(fill='x', pady=5)

        ttk.Label(shape_frame, text="QR Shape:").pack(side='left')
        shape_combo = ttk.Combobox(shape_frame, textvariable=self.qr_shape,
                                   values=["squares", "dots",
                                           "rounded", "circles"],
                                   state='readonly')
        shape_combo.pack(side='left', padx=5)
        shape_combo.bind('<<ComboboxSelected>>', self.update_real_time_preview)

        # Export tab
        export_tab = ttk.Frame(notebook)
        notebook.add(export_tab, text="Export")

        export_buttons = [
            ("Export as PNG", self.export_png),
            ("Export as SVG", self.export_svg),
            ("Export as PDF", self.export_pdf),
            ("High-Res Print", self.export_high_res)
        ]

        for text, command in export_buttons:
            ttk.Button(export_tab, text=text, command=command).pack(pady=5)

    def show_scanner_tab(self):
        """Show QR code scanner tab"""
        self.clear_content()

        scanner_frame = ttk.LabelFrame(
            self.content_frame, text="QR Code Scanner", padding=15)
        scanner_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Camera feed
        camera_frame = ttk.Frame(scanner_frame)
        camera_frame.pack(fill='both', expand=True, pady=10)

        self.camera_label = ttk.Label(camera_frame, text="Camera feed will appear here",
                                      background='black', foreground='white')
        self.camera_label.pack(fill='both', expand=True)

        # Controls
        controls_frame = ttk.Frame(scanner_frame)
        controls_frame.pack(fill='x', pady=10)

        ttk.Button(controls_frame, text="Start Camera",
                   command=self.start_camera, style='Success.TButton').pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Stop Camera",
                   command=self.stop_camera).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Upload Image to Scan",
                   command=self.scan_from_image).pack(side='left', padx=5)

        # Results
        self.scan_result = scrolledtext.ScrolledText(scanner_frame, height=4)
        self.scan_result.pack(fill='x', pady=10)

    def show_datatype_tab(self):
        """Show data type specific QR generation"""
        self.clear_content()

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Contact Card
        contact_tab = ttk.Frame(notebook)
        notebook.add(contact_tab, text="Contact Card")
        self.setup_contact_form(contact_tab)

        # Email
        email_tab = ttk.Frame(notebook)
        notebook.add(email_tab, text="Email")
        self.setup_email_form(email_tab)

        # WiFi
        wifi_tab = ttk.Frame(notebook)
        notebook.add(wifi_tab, text="WiFi")
        self.setup_wifi_form(wifi_tab)

        # Social Media
        social_tab = ttk.Frame(notebook)
        notebook.add(social_tab, text="Social Media")
        self.setup_social_form(social_tab)

    def setup_contact_form(self, parent):
        """Setup contact card form"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)

        fields = [
            ("First Name", "contact_first"),
            ("Last Name", "contact_last"),
            ("Phone", "contact_phone"),
            ("Email", "contact_email"),
            ("Company", "contact_company"),
            ("Title", "contact_title")
        ]

        self.contact_vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(
                row=i, column=0, sticky='w', pady=5)
            var = tk.StringVar()
            entry = ttk.Entry(form_frame, textvariable=var, width=30)
            entry.grid(row=i, column=1, sticky='ew', pady=5, padx=5)
            self.contact_vars[key] = var

        ttk.Button(form_frame, text="Generate Contact QR",
                   command=self.generate_contact_qr, style='Success.TButton').grid(row=len(fields), column=0, columnspan=2, pady=10)

    def setup_email_form(self, parent):
        """Setup email QR form"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(form_frame, text="Email:").grid(
            row=0, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(
            row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(form_frame, text="Subject:").grid(
            row=1, column=0, sticky='w', pady=5)
        self.email_subject_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_subject_var, width=30).grid(
            row=1, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(form_frame, text="Body:").grid(
            row=2, column=0, sticky='w', pady=5)
        self.email_body_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_body_var, width=30).grid(
            row=2, column=1, sticky='ew', pady=5, padx=5)

        ttk.Button(form_frame, text="Generate Email QR",
                   command=self.generate_email_qr, style='Success.TButton').grid(row=3, column=0, columnspan=2, pady=10)

    def setup_wifi_form(self, parent):
        """Setup WiFi QR form"""
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(form_frame, text="Network Name (SSID):").grid(
            row=0, column=0, sticky='w', pady=5)
        self.wifi_name = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.wifi_name, width=30).grid(
            row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(form_frame, text="Password:").grid(
            row=1, column=0, sticky='w', pady=5)
        self.wifi_pass = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.wifi_pass, show="•", width=30).grid(
            row=1, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(form_frame, text="Security Type:").grid(
            row=2, column=0, sticky='w', pady=5)
        self.wifi_security = tk.StringVar(value="WPA")
        ttk.Combobox(form_frame, textvariable=self.wifi_security,
                     values=["WPA", "WEP", "nopass"], state='readonly').grid(row=2, column=1, sticky='w', pady=5, padx=5)

        ttk.Button(form_frame, text="Generate WiFi QR",
                   command=self.generate_wifi_qr, style='Success.TButton').grid(row=3, column=0, columnspan=2, pady=10)

    def setup_social_form(self, parent):
        """Setup social media QR forms"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)

        platforms = ["Instagram", "Facebook",
                     "Twitter", "YouTube", "TikTok", "LinkedIn"]

        for platform in platforms:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=platform)

            ttk.Label(tab, text=f"{platform} Username/URL:").pack(pady=10)
            var = tk.StringVar()
            entry = ttk.Entry(tab, textvariable=var, width=30)
            entry.pack(pady=5)

            ttk.Button(tab, text=f"Generate {platform} QR",
                       command=lambda p=platform, v=var: self.generate_social_qr(
                           p, v),
                       style='Primary.TButton').pack(pady=10)

    def show_bulk_tab(self):
        """Show bulk QR generation tab"""
        self.clear_content()

        bulk_frame = ttk.LabelFrame(
            self.content_frame, text="Bulk QR Code Generation", padding=15)
        bulk_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # CSV upload
        ttk.Label(bulk_frame, text="Upload CSV File:").pack(anchor='w', pady=5)
        ttk.Button(bulk_frame, text="Select CSV File",
                   command=self.select_csv_file, style='Primary.TButton').pack(pady=10)

        self.csv_file_label = ttk.Label(
            bulk_frame, text="No file selected", foreground='gray')
        self.csv_file_label.pack(pady=5)

        # Preview area
        ttk.Label(bulk_frame, text="Data Preview:").pack(anchor='w', pady=10)
        self.bulk_preview = scrolledtext.ScrolledText(bulk_frame, height=8)
        self.bulk_preview.pack(fill='both', expand=True, pady=5)

        # Generation options
        options_frame = ttk.Frame(bulk_frame)
        options_frame.pack(fill='x', pady=10)

        ttk.Label(options_frame, text="Naming Template:").pack(side='left')
        self.naming_template = tk.StringVar(value="{name}_{date}")
        ttk.Entry(options_frame, textvariable=self.naming_template,
                  width=30).pack(side='left', padx=5)

        ttk.Button(bulk_frame, text="Generate Bulk QR Codes",
                   command=self.generate_bulk_qr, style='Success.TButton').pack(pady=20)

    def show_business_tab(self):
        """Show business features tab"""
        self.clear_content()

        business_frame = ttk.LabelFrame(
            self.content_frame, text="Business Features", padding=15)
        business_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Branding templates
        branding_frame = ttk.LabelFrame(
            business_frame, text="Branding Templates", padding=10)
        branding_frame.pack(fill='x', pady=10)

        ttk.Button(branding_frame, text="Add Company Logo",
                   command=self.add_company_logo).pack(pady=5)
        ttk.Button(branding_frame, text="Set Brand Colors",
                   command=self.set_brand_colors).pack(pady=5)

        # Poster generator
        poster_frame = ttk.LabelFrame(
            business_frame, text="Poster Generator", padding=10)
        poster_frame.pack(fill='x', pady=10)

        ttk.Button(poster_frame, text="Generate QR Poster",
                   command=self.generate_poster).pack(pady=5)

    def show_security_tab(self):
        """Show security features tab"""
        self.clear_content()

        security_frame = ttk.LabelFrame(
            self.content_frame, text="Security Features", padding=15)
        security_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Password protection
        ttk.Label(security_frame, text="Password Protection:").pack(
            anchor='w', pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(security_frame, textvariable=self.password_var,
                  show="•", width=30).pack(anchor='w', pady=5)

        ttk.Button(security_frame, text="Generate Secure QR",
                   command=self.generate_secure_qr, style='Success.TButton').pack(pady=10)

    def show_smart_tab(self):
        """Show smart features tab"""
        self.clear_content()

        smart_frame = ttk.LabelFrame(
            self.content_frame, text="Smart Features", padding=15)
        smart_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # AI features
        ttk.Button(smart_frame, text="AI Text Cleaner",
                   command=self.ai_clean_text, style='Primary.TButton').pack(pady=5)
        ttk.Button(smart_frame, text="Remove Tracking Parameters",
                   command=self.remove_tracking_params, style='Primary.TButton').pack(pady=5)
        ttk.Button(smart_frame, text="Auto WiFi QR",
                   command=self.auto_wifi_qr, style='Primary.TButton').pack(pady=5)

        # Voice input
        ttk.Button(smart_frame, text="Voice Input",
                   command=self.voice_input, style='Accent.TButton').pack(pady=10)

    def show_creative_tab(self):
        """Show creative features tab"""
        self.clear_content()

        creative_frame = ttk.LabelFrame(
            self.content_frame, text="Creative Features", padding=15)
        creative_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Eye patterns
        ttk.Label(creative_frame, text="Eye Patterns:").pack(
            anchor='w', pady=5)
        self.eye_pattern = tk.StringVar(value="default")
        eye_combo = ttk.Combobox(creative_frame, textvariable=self.eye_pattern,
                                 values=["default", "circle", "rounded", "diamond"])
        eye_combo.pack(anchor='w', pady=5)

        # Animated QR
        ttk.Button(creative_frame, text="Create Animated QR",
                   command=self.create_animated_qr, style='Primary.TButton').pack(pady=10)

    def show_history_tab(self):
        """Show history tab"""
        self.clear_content()

        history_frame = ttk.LabelFrame(
            self.content_frame, text="Generation History", padding=15)
        history_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # History list with thumbnails
        self.history_tree = ttk.Treeview(history_frame, columns=(
            'Date', 'Type', 'Preview'), show='tree headings')
        self.history_tree.heading('#0', text='Data')
        self.history_tree.heading('Date', text='Date')
        self.history_tree.heading('Type', text='Type')
        self.history_tree.pack(fill='both', expand=True, pady=10)

        # History controls
        controls_frame = ttk.Frame(history_frame)
        controls_frame.pack(fill='x', pady=10)

        ttk.Button(controls_frame, text="Regenerate Selected",
                   command=self.regenerate_from_history, style='Primary.TButton').pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Clear History",
                   command=self.clear_history, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Export History",
                   command=self.export_history, style='Primary.TButton').pack(side='left', padx=5)

    def show_settings_tab(self):
        """Show settings tab"""
        self.clear_content()

        settings_frame = ttk.LabelFrame(
            self.content_frame, text="Settings & Preferences", padding=15)
        settings_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Language selection
        ttk.Label(settings_frame, text="Language:").pack(anchor='w', pady=5)
        self.language_var = tk.StringVar(value="English")
        lang_combo = ttk.Combobox(settings_frame, textvariable=self.language_var,
                                  values=["English", "Spanish", "French", "German"])
        lang_combo.pack(anchor='w', pady=5)

        # Auto-save
        self.auto_save = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Auto-save preferences",
                        variable=self.auto_save).pack(anchor='w', pady=5)

        # Save button
        ttk.Button(settings_frame, text="Save Preferences",
                   command=self.save_preferences, style='Success.TButton').pack(pady=20)

    # Core functionality implementations
    def update_real_time_preview(self, event=None):
        """Update QR code preview in real-time"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if len(data) < 3:  # Minimum data length
            return

        # Detect data type
        data_type = self.detect_data_type(data)
        self.data_type_label.config(text=data_type)

        # Generate preview in thread to avoid UI freeze
        threading.Thread(target=self.generate_preview,
                         args=(data,), daemon=True).start()

    def detect_data_type(self, data):
        """Detect the type of data for smart preview"""
        if data.startswith('http'):
            return "URL"
        elif '@' in data and '.' in data:
            return "Email"
        elif data.startswith('WIFI:'):
            return "WiFi"
        elif data.startswith('BEGIN:VCARD'):
            return "Contact"
        else:
            return "Text"

    def generate_preview(self, data):
        """Generate preview QR code"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color=self.fill_color.get(),
                                back_color=self.bg_color.get() if not self.transparent_bg.get() else None)

            # Apply gradient if enabled
            if self.use_gradient.get():
                img = self.apply_gradient_effect(img)

            # Resize for preview
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Update UI in main thread
            self.root.after(0, lambda: self.update_preview_image(photo))

        except Exception as e:
            print(f"Preview generation error: {e}")

    def update_preview_image(self, photo):
        """Update preview image in UI"""
        self.preview_label.configure(image=photo)
        self.preview_label.image = photo

    def apply_gradient_effect(self, img):
        """Apply gradient effect to QR code"""
        # Convert to numpy array for processing
        img_array = np.array(img.convert('RGB'))

        # Create gradient
        height, width = img_array.shape[0], img_array.shape[1]
        gradient = np.zeros((height, width, 3), dtype=np.uint8)

        # Simple horizontal gradient
        for i in range(width):
            ratio = i / width
            r = int((1 - ratio) * int(self.gradient_start.get()[1:3], 16) +
                    ratio * int(self.gradient_end.get()[1:3], 16))
            g = int((1 - ratio) * int(self.gradient_start.get()[3:5], 16) +
                    ratio * int(self.gradient_end.get()[3:5], 16))
            b = int((1 - ratio) * int(self.gradient_start.get()[5:7], 16) +
                    ratio * int(self.gradient_end.get()[5:7], 16))

            gradient[:, i] = [r, g, b]

        # Apply gradient only to black pixels (QR code parts)
        mask = img_array.mean(axis=2) < 128  # Black pixels
        result = np.where(mask[:, :, None], gradient, img_array)

        return Image.fromarray(result)

    def choose_fill_color(self):
        """Choose fill color for QR code"""
        color = colorchooser.askcolor(
            title="Choose Fill Color", initialcolor=self.fill_color.get())[1]
        if color:
            self.fill_color.set(color)
            self.fill_color_label.configure(foreground=color)
            self.update_real_time_preview()

    def choose_bg_color(self):
        """Choose background color"""
        color = colorchooser.askcolor(
            title="Choose Background Color", initialcolor=self.bg_color.get())[1]
        if color:
            self.bg_color.set(color)
            self.bg_color_label.configure(foreground=color)
            self.update_real_time_preview()

    def choose_gradient_color(self, which):
        """Choose gradient color"""
        color = colorchooser.askcolor(
            title=f"Choose {which.capitalize()} Color")[1]
        if color:
            if which == 'start':
                self.gradient_start.set(color)
            else:
                self.gradient_end.set(color)
            self.update_real_time_preview()

    def start_camera(self):
        """Start camera for QR scanning"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Could not access camera")
                return
            self.camera_active = True
            self.update_camera_feed()
        except Exception as e:
            messagebox.showerror(
                "Camera Error", f"Failed to start camera: {str(e)}")

    def stop_camera(self):
        """Stop camera"""
        self.camera_active = False
        if self.cap:
            self.cap.release()
        self.camera_label.configure(text="Camera stopped")

    def update_camera_feed(self):
        """Update camera feed for QR scanning"""
        if self.camera_active and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Convert to RGB and detect QR codes
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # QR code detection
                detector = cv2.QRCodeDetector()
                data, bbox, _ = detector.detectAndDecode(rgb_frame)

                if bbox is not None:
                    # Draw bounding box
                    bbox = bbox.astype(int)
                    for i in range(len(bbox)):
                        cv2.line(rgb_frame, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]),
                                 color=(255, 0, 0), thickness=2)

                    if data:
                        self.scan_result.delete('1.0', tk.END)
                        self.scan_result.insert('1.0', f"Scanned: {data}")

                # Convert to PhotoImage and update label
                img = Image.fromarray(rgb_frame)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                self.camera_label.configure(image=photo)
                self.camera_label.image = photo

            # Continue updating
            if self.camera_active:
                self.root.after(10, self.update_camera_feed)

    def scan_from_image(self):
        """Scan QR code from uploaded image"""
        path = filedialog.askopenfilename(
            title="Select Image with QR Code",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if path:
            img = cv2.imread(path)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(img)

            if data:
                self.scan_result.delete('1.0', tk.END)
                self.scan_result.insert('1.0', f"Scanned: {data}")
            else:
                messagebox.showwarning(
                    "Scan Failed", "No QR code found in the image")

    def generate_contact_qr(self):
        """Generate contact card QR"""
        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{self.contact_vars['contact_first'].get()} {self.contact_vars['contact_last'].get()}
TEL:{self.contact_vars['contact_phone'].get()}
EMAIL:{self.contact_vars['contact_email'].get()}
ORG:{self.contact_vars['contact_company'].get()}
TITLE:{self.contact_vars['contact_title'].get()}
END:VCARD"""

        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', vcard)
        self.generate_qr()

    def generate_email_qr(self):
        """Generate email QR"""
        email_data = f"mailto:{self.email_var.get()}?subject={self.email_subject_var.get()}&body={self.email_body_var.get()}"
        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', email_data)
        self.generate_qr()

    def generate_wifi_qr(self):
        """Generate WiFi QR"""
        wifi_string = f"WIFI:T:{self.wifi_security.get()};S:{self.wifi_name.get()};P:{self.wifi_pass.get()};;"
        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', wifi_string)
        self.generate_qr()

    def generate_social_qr(self, platform, var):
        """Generate social media QR"""
        username = var.get().strip()
        if not username:
            messagebox.showerror(
                "Error", f"Please enter {platform} username/URL")
            return

        # Basic URL generation
        urls = {
            "Instagram": f"https://instagram.com/{username}",
            "Facebook": f"https://facebook.com/{username}",
            "Twitter": f"https://twitter.com/{username}",
            "YouTube": f"https://youtube.com/{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            "LinkedIn": f"https://linkedin.com/in/{username}"
        }

        url = urls.get(platform, username)
        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', url)
        self.generate_qr()

    def select_csv_file(self):
        """Select CSV file for bulk generation"""
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path:
            self.bulk_file_path = path
            self.csv_file_label.configure(
                text=f"Selected: {os.path.basename(path)}")
            self.preview_csv_data(path)

    def preview_csv_data(self, path):
        """Preview CSV data"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            preview_text = f"Columns: {', '.join(reader.fieldnames)}\n\n"
            preview_text += "First 5 rows:\n"
            for i, row in enumerate(rows[:5]):
                preview_text += f"{i+1}. {str(row)}\n"

            self.bulk_preview.delete('1.0', tk.END)
            self.bulk_preview.insert('1.0', preview_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {str(e)}")

    def generate_bulk_qr(self):
        """Generate bulk QR codes from CSV"""
        if not hasattr(self, 'bulk_file_path'):
            messagebox.showerror("Error", "Please select a CSV file first!")
            return

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        try:
            with open(self.bulk_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            success_count = 0
            for i, row in enumerate(rows):
                try:
                    # Use first column as data, or customize as needed
                    data = list(row.values())[0]

                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_H,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(data)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")

                    # Generate filename from template
                    filename = self.naming_template.get().format(
                        name=row.get('name', f'qr_{i+1:03d}'),
                        date=datetime.now().strftime("%Y%m%d"),
                        index=i+1
                    ) + ".png"

                    filepath = os.path.join(output_dir, filename)
                    img.save(filepath)
                    success_count += 1

                except Exception as e:
                    print(f"Failed to generate QR for row {i+1}: {str(e)}")

            # Create ZIP file
            zip_path = os.path.join(output_dir, "qr_codes.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in os.listdir(output_dir):
                    if file.endswith('.png'):
                        zipf.write(os.path.join(output_dir, file), file)

            messagebox.showinfo("Bulk Generation Complete",
                                f"Successfully generated {success_count} QR codes!\nZIP file created: qr_codes.zip")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to process bulk generation: {str(e)}")

    def generate_secure_qr(self):
        """Generate password-protected QR"""
        password = self.password_var.get()
        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return

        data = self.entry_data.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter data to encode")
            return

        # Simple encryption (in real app, use proper encryption)
        encrypted_data = f"ENCRYPTED:{password}:{data}"
        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', encrypted_data)
        self.generate_qr()

    def ai_clean_text(self):
        """AI text cleaning (placeholder)"""
        data = self.entry_data.get("1.0", tk.END).strip()
        # Simple cleaning - remove extra whitespace
        cleaned = ' '.join(data.split())
        self.entry_data.delete('1.0', tk.END)
        self.entry_data.insert('1.0', cleaned)
        messagebox.showinfo("AI Clean", "Text cleaned successfully!")

    def remove_tracking_params(self):
        """Remove tracking parameters from URLs"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if data.startswith('http'):
            # Remove common tracking parameters
            import urllib.parse
            from urllib.parse import urlparse, parse_qs, urlunparse

            parsed = urlparse(data)
            query_params = parse_qs(parsed.query)

            # Parameters to keep (remove tracking parameters)
            keep_params = ['id', 'page', 'category']  # Customize as needed
            filtered_params = {k: v for k,
                               v in query_params.items() if k in keep_params}

            # Reconstruct URL
            filtered_query = urllib.parse.urlencode(
                filtered_params, doseq=True)
            clean_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, filtered_query, parsed.fragment
            ))

            self.entry_data.delete('1.0', tk.END)
            self.entry_data.insert('1.0', clean_url)
            messagebox.showinfo("Tracking Removed",
                                "Tracking parameters removed!")
        else:
            messagebox.showwarning(
                "Not a URL", "This feature works with URLs only")

    def auto_wifi_qr(self):
        """Auto-generate WiFi QR from system (placeholder)"""
        messagebox.showinfo(
            "Auto WiFi", "This would automatically detect your WiFi settings in a full implementation")

    def voice_input(self):
        """Voice input (placeholder)"""
        messagebox.showinfo(
            "Voice Input", "Voice input would be implemented here with speech recognition")

    def create_animated_qr(self):
        """Create animated QR code (placeholder)"""
        messagebox.showinfo(
            "Animated QR", "Animated QR creation would be implemented here")

    def export_png(self):
        """Export as PNG"""
        self.generate_qr()

    def export_svg(self):
        """Export as SVG"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter data first")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg")],
            title="Save as SVG"
        )

        if save_path:
            try:
                # Create SVG QR code
                factory = qrcode.image.svg.SvgImage
                img = qrcode.make(data, image_factory=factory)
                img.save(save_path)
                messagebox.showinfo("Success", f"SVG saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save SVG: {str(e)}")

    def export_pdf(self):
        """Export as PDF"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter data first")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save as PDF"
        )

        if save_path:
            try:
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=10,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                # Save temporary image
                temp_img = "temp_qr.png"
                img.save(temp_img)

                # Create PDF
                c = canvas.Canvas(save_path, pagesize=letter)
                c.drawImage(temp_img, 100, 500, width=200, height=200)
                c.setFont("Helvetica", 12)
                c.drawString(100, 480, f"QR Code: {data[:50]}...")
                c.save()

                # Clean up
                os.remove(temp_img)
                messagebox.showinfo("Success", f"PDF saved to {save_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")

    def export_high_res(self):
        """Export high-resolution version"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter data first")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            title="Save High-Res QR"
        )

        if save_path:
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=20,  # Larger for high resolution
                    border=8,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(save_path, dpi=(300, 300))  # High DPI
                messagebox.showinfo(
                    "Success", f"High-res QR saved to {save_path}")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to save high-res QR: {str(e)}")

    def generate_qr(self):
        """Main QR generation function"""
        data = self.entry_data.get("1.0", tk.END).strip()
        if not data:
            messagebox.showerror("Error", "Please enter some text or URL!")
            return

        try:
            # Map error correction
            error_correction_map = {
                "L (Low)": qrcode.constants.ERROR_CORRECT_L,
                "M (Medium)": qrcode.constants.ERROR_CORRECT_M,
                "Q (Quartile)": qrcode.constants.ERROR_CORRECT_Q,
                "H (High)": qrcode.constants.ERROR_CORRECT_H
            }

            ec_level = error_correction_map.get(
                self.error_correction.get(), qrcode.constants.ERROR_CORRECT_H)

            qr = qrcode.QRCode(
                version=1,
                error_correction=ec_level,
                box_size=10,
                border=self.border_size.get(),
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color=self.fill_color.get(),
                                back_color=self.bg_color.get() if not self.transparent_bg.get() else None)

            # Apply gradient if enabled
            if self.use_gradient.get():
                img = self.apply_gradient_effect(img)

            # Add logo if selected
            if self.logo_path.get():
                try:
                    logo = Image.open(self.logo_path.get())
                    # Resize logo to 20% of QR code size
                    qr_size = min(img.size) // 5
                    logo = logo.resize((qr_size, qr_size),
                                       Image.Resampling.LANCZOS)

                    # Create circular mask for logo
                    mask = Image.new('L', (qr_size, qr_size), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, qr_size, qr_size), fill=255)

                    # Paste logo with mask
                    pos = ((img.size[0] - qr_size) // 2,
                           (img.size[1] - qr_size) // 2)
                    img.paste(logo, pos, mask)
                except Exception as e:
                    messagebox.showwarning(
                        "Logo Error", f"Could not add logo: {str(e)}")

            # Save the QR code
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Save QR Code"
            )

            if save_path:
                img.save(save_path)
                self.add_to_history(data, save_path)
                messagebox.showinfo(
                    "Success", f"QR code saved successfully!\nLocation: {save_path}")

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to generate QR code: {str(e)}")

    def add_company_logo(self):
        """Add company logo for branding"""
        path = filedialog.askopenfilename(
            title="Select Company Logo",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if path:
            self.logo_path.set(path)
            messagebox.showinfo(
                "Logo Added", "Company logo added successfully!")

    def set_brand_colors(self):
        """Set brand colors"""
        color = colorchooser.askcolor(title="Choose Brand Color")[1]
        if color:
            self.fill_color.set(color)
            self.update_real_time_preview()

    def generate_poster(self):
        """Generate QR poster"""
        messagebox.showinfo("Poster Generator",
                            "Poster generation would be implemented here")

    def clear_content(self):
        """Clear content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.current_theme = "dark" if self.dark_mode.get() else "light"
        self.apply_theme()

    def apply_theme(self):
        """Apply current theme"""
        self.configure_styles()
        theme = self.theme_colors[self.current_theme]
        self.root.configure(bg=theme['bg'])

    def add_to_history(self, data, filepath):
        """Add generation to history"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_entry = {
            "timestamp": timestamp,
            "data": data,
            "filepath": filepath,
            "type": self.detect_data_type(data)
        }

        self.history_data.append(history_entry)
        self.save_history()

    def regenerate_from_history(self):
        """Regenerate selected QR code from history"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning", "Please select an item from history!")
            return

        # Implementation for regeneration from history
        pass

    def clear_history(self):
        """Clear generation history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            self.history_data.clear()
            self.save_history()

    def export_history(self):
        """Export history to file"""
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export History"
        )
        if save_path:
            try:
                with open(save_path, 'w') as f:
                    json.dump(self.history_data, f, indent=2)
                messagebox.showinfo(
                    "Success", "History exported successfully!")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Failed to export history: {str(e)}")

    def save_history(self):
        """Save history to file"""
        try:
            with open("qr_history.json", "w") as f:
                json.dump(self.history_data, f)
        except:
            pass

    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists("qr_history.json"):
                with open("qr_history.json", "r") as f:
                    self.history_data = json.load(f)
        except:
            self.history_data = []

    def save_preferences(self):
        """Save user preferences"""
        self.user_preferences = {
            "theme": self.current_theme,
            "language": self.language_var.get(),
            "auto_save": self.auto_save.get()
        }

        try:
            with open("user_preferences.json", "w") as f:
                json.dump(self.user_preferences, f)
            messagebox.showinfo("Success", "Preferences saved successfully!")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to save preferences: {str(e)}")

    def load_preferences(self):
        """Load user preferences"""
        try:
            if os.path.exists("user_preferences.json"):
                with open("user_preferences.json", "r") as f:
                    self.user_preferences = json.load(f)

                # Apply preferences
                if "theme" in self.user_preferences:
                    self.dark_mode.set(
                        self.user_preferences["theme"] == "dark")
                    self.toggle_theme()

                if "language" in self.user_preferences:
                    self.language_var.set(self.user_preferences["language"])

        except:
            self.user_preferences = {}


def main():
    root = tk.Tk()
    app = ModernQRGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
