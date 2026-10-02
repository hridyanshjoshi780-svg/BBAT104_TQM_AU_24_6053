"""
Library Management System GUI (BBAT104 TQM Project - Roll No: 2410301031)
Q04 Security Enhancements: Role-Based Login, Password Encryption, Input Validation,
Password Reset, Audit Trail, and SQC Control Charts.
"""

import sys
import os

# Check for tkinter availability early
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from database import init_db
from auth import (
    authenticate_user, register_user, reset_password,
    log_audit_trail, ValidationError
)
from library_service import (
    search_books, get_all_categories, add_book, issue_book,
    return_book, get_borrow_records, get_audit_logs
)
from sqc_analysis import generate_sqc_chart


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.current_user = None

        if CTK_AVAILABLE:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")
            self.root.title("BBAT104 TQM Library Management System (Q04)")
            self.root.geometry("1050x680")
            self.root.minsize(900, 600)
        else:
            self.root.title("BBAT104 TQM Library Management System (Q04)")
            self.root.geometry("1050x680")

        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        self.show_login_view()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # =========================================================================
    # LOGIN / AUTHENTICATION VIEW
    # =========================================================================
    def show_login_view(self):
        self.clear_container()

        bg_color = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        text_color = "#ffffff" if CTK_AVAILABLE else "#1a202c"
        subtext_color = "#94a3b8" if CTK_AVAILABLE else "#718096"

        self.main_container.configure(bg=bg_color)

        # Center frame
        center_frame = tk.Frame(self.main_container, bg=bg_color)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title Card
        title_label = tk.Label(
            center_frame,
            text="📚 BBAT104 Library Management System",
            font=("Helvetica", 18, "bold"),
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(0, 4))

        subtitle_label = tk.Label(
            center_frame,
            text="Total Quality Management (TQM) — Q04 Security Suite",
            font=("Helvetica", 10),
            bg=bg_color,
            fg=subtext_color
        )
        subtitle_label.pack(pady=(0, 16))

        # Login Form Card
        card = tk.Frame(center_frame, bg=card_bg, padx=30, pady=25, relief="ridge", bd=1)
        card.pack(fill="both", expand=True)

        # Role Selector
        tk.Label(card, text="Role", font=("Helvetica", 10, "bold"), bg=card_bg, fg=text_color).pack(anchor="w", pady=(0, 2))
        self.role_var = tk.StringVar(value="student")
        role_frame = tk.Frame(card, bg=card_bg)
        role_frame.pack(fill="x", pady=(0, 10))

        tk.Radiobutton(
            role_frame, text="Student", variable=self.role_var, value="student",
            bg=card_bg, fg=text_color, selectcolor=card_bg, activebackground=card_bg
        ).pack(side="left", padx=(0, 20))
        tk.Radiobutton(
            role_frame, text="Admin", variable=self.role_var, value="admin",
            bg=card_bg, fg=text_color, selectcolor=card_bg, activebackground=card_bg
        ).pack(side="left")

        # Username
        tk.Label(card, text="Username", font=("Helvetica", 10, "bold"), bg=card_bg, fg=text_color).pack(anchor="w", pady=(5, 2))
        self.username_entry = tk.Entry(card, font=("Helvetica", 11), width=32, bg="#333948" if CTK_AVAILABLE else "#ffffff", fg=text_color, insertbackground=text_color)
        self.username_entry.pack(pady=(0, 10), ipady=4)
        self.username_entry.insert(0, "student1")

        # Password
        tk.Label(card, text="Password", font=("Helvetica", 10, "bold"), bg=card_bg, fg=text_color).pack(anchor="w", pady=(5, 2))
        self.password_entry = tk.Entry(card, show="•", font=("Helvetica", 11), width=32, bg="#333948" if CTK_AVAILABLE else "#ffffff", fg=text_color, insertbackground=text_color)
        self.password_entry.pack(pady=(0, 5), ipady=4)
        self.password_entry.insert(0, "student123")

        # Show password toggle
        self.show_pw_var = tk.BooleanVar(value=False)
        def toggle_password():
            self.password_entry.config(show="" if self.show_pw_var.get() else "•")

        tk.Checkbutton(
            card, text="Show password", variable=self.show_pw_var, command=toggle_password,
            bg=card_bg, fg=subtext_color, selectcolor=card_bg, activebackground=card_bg, font=("Helvetica", 9)
        ).pack(anchor="w", pady=(0, 12))

        # Status Message
        self.login_status = tk.Label(card, text="", font=("Helvetica", 9), bg=card_bg, fg="#e74c3c")
        self.login_status.pack(pady=(0, 8))

        # Login Button
        login_btn = tk.Button(
            card, text="Sign In", font=("Helvetica", 11, "bold"),
            bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff",
            width=28, height=1, cursor="hand2", bd=0, command=self.handle_login
        )
        login_btn.pack(pady=(0, 10))

        # Secondary Links (Register & Reset)
        links_frame = tk.Frame(card, bg=card_bg)
        links_frame.pack(fill="x", pady=(5, 0))

        register_btn = tk.Button(
            links_frame, text="Create Account", font=("Helvetica", 9, "underline"),
            bg=card_bg, fg="#38bdf8", bd=0, cursor="hand2", command=self.open_register_dialog
        )
        register_btn.pack(side="left")

        reset_btn = tk.Button(
            links_frame, text="Forgot Password?", font=("Helvetica", 9, "underline"),
            bg=card_bg, fg=subtext_color, bd=0, cursor="hand2", command=self.open_reset_dialog
        )
        reset_btn.pack(side="right")

        # Demo Credentials hint
        hint_label = tk.Label(
            center_frame,
            text="Demo: student1 / student123  |  admin / admin123",
            font=("Helvetica", 8),
            bg=bg_color,
            fg=subtext_color
        )
        hint_label.pack(pady=(12, 0))

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        user = authenticate_user(username, password, expected_role=role)
        if user:
            self.current_user = user
            self.show_dashboard_view()
        else:
            self.login_status.config(text="Invalid credentials or role mismatch.", fg="#e74c3c")

    def open_register_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Register New Account")
        win.geometry("380x420")
        win.resizable(False, False)

        bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"
        win.configure(bg=bg)

        tk.Label(win, text="Create Library Account", font=("Helvetica", 14, "bold"), bg=bg, fg=fg).pack(pady=(15, 10))

        frame = tk.Frame(win, bg=bg, padx=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Full Name", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        name_ent = tk.Entry(frame, width=32, font=("Helvetica", 10))
        name_ent.pack(pady=(2, 8))

        tk.Label(frame, text="Username (3-20 chars)", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        user_ent = tk.Entry(frame, width=32, font=("Helvetica", 10))
        user_ent.pack(pady=(2, 8))

        tk.Label(frame, text="Email Address", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        email_ent = tk.Entry(frame, width=32, font=("Helvetica", 10))
        email_ent.pack(pady=(2, 8))

        tk.Label(frame, text="Password (min 6 chars)", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        pw_ent = tk.Entry(frame, show="•", width=32, font=("Helvetica", 10))
        pw_ent.pack(pady=(2, 8))

        err_label = tk.Label(frame, text="", bg=bg, fg="#e74c3c", font=("Helvetica", 8))
        err_label.pack(pady=(0, 5))

        def submit_reg():
            try:
                register_user(
                    username=user_ent.get(),
                    password=pw_ent.get(),
                    full_name=name_ent.get(),
                    email=email_ent.get(),
                    role="student"
                )
                messagebox.showinfo("Success", "Account created successfully! You may now log in.")
                win.destroy()
            except ValidationError as e:
                err_label.config(text=str(e))

        tk.Button(frame, text="Register", bg="#2563eb", fg="#ffffff", font=("Helvetica", 10, "bold"),
                  command=submit_reg, width=20, cursor="hand2").pack(pady=10)

    def open_reset_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Password Reset (Q04)")
        win.geometry("380x350")
        win.resizable(False, False)

        bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"
        win.configure(bg=bg)

        tk.Label(win, text="Self-Service Password Reset", font=("Helvetica", 13, "bold"), bg=bg, fg=fg).pack(pady=(15, 10))

        frame = tk.Frame(win, bg=bg, padx=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Username", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        user_ent = tk.Entry(frame, width=32, font=("Helvetica", 10))
        user_ent.pack(pady=(2, 8))

        tk.Label(frame, text="Registered Email", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        email_ent = tk.Entry(frame, width=32, font=("Helvetica", 10))
        email_ent.pack(pady=(2, 8))

        tk.Label(frame, text="New Password", bg=bg, fg=fg, font=("Helvetica", 9, "bold")).pack(anchor="w")
        pw_ent = tk.Entry(frame, show="•", width=32, font=("Helvetica", 10))
        pw_ent.pack(pady=(2, 8))

        err_label = tk.Label(frame, text="", bg=bg, fg="#e74c3c", font=("Helvetica", 8))
        err_label.pack(pady=(0, 5))

        def submit_reset():
            try:
                reset_password(user_ent.get(), email_ent.get(), pw_ent.get())
                messagebox.showinfo("Success", "Password updated successfully!")
                win.destroy()
            except ValidationError as e:
                err_label.config(text=str(e))

        tk.Button(frame, text="Update Password", bg="#2563eb", fg="#ffffff", font=("Helvetica", 10, "bold"),
                  command=submit_reset, width=20, cursor="hand2").pack(pady=10)

    # =========================================================================
    # MAIN DASHBOARD VIEW
    # =========================================================================
    def show_dashboard_view(self):
        self.clear_container()

        bg_color = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        sidebar_bg = "#181b24" if CTK_AVAILABLE else "#2d3748"
        header_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        text_color = "#ffffff" if CTK_AVAILABLE else "#1a202c"
        accent_color = "#38bdf8"

        self.main_container.configure(bg=bg_color)

        # Top Bar
        top_bar = tk.Frame(self.main_container, bg=header_bg, height=52)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        role_badge = "🛡️ ADMIN" if self.current_user["role"] == "admin" else "🎓 STUDENT"
        title_text = f"📚 Library Management System  |  {role_badge}: {self.current_user['full_name']} (@{self.current_user['username']})"
        tk.Label(top_bar, text=title_text, font=("Helvetica", 11, "bold"), bg=header_bg, fg=text_color).pack(side="left", padx=16)

        logout_btn = tk.Button(
            top_bar, text="Logout", font=("Helvetica", 9, "bold"),
            bg="#dc2626", fg="#ffffff", bd=0, padx=12, pady=4, cursor="hand2",
            command=self.logout
        )
        logout_btn.pack(side="right", padx=16)

        # Body Frame (Sidebar + Content)
        body_frame = tk.Frame(self.main_container, bg=bg_color)
        body_frame.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(body_frame, bg=sidebar_bg, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="NAVIGATION", font=("Helvetica", 9, "bold"), bg=sidebar_bg, fg="#64748b").pack(anchor="w", padx=16, pady=(16, 8))

        # Dynamic Content View
        self.content_area = tk.Frame(body_frame, bg=bg_color)
        self.content_area.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        def make_nav_btn(text, cmd):
            return tk.Button(
                sidebar, text=text, font=("Helvetica", 10),
                bg=sidebar_bg, fg="#e2e8f0", bd=0, activebackground="#2a3040", activeforeground="#ffffff",
                anchor="w", padx=16, pady=8, cursor="hand2", command=cmd
            )

        make_nav_btn("📖 Book Catalog", self.render_catalog_view).pack(fill="x")
        make_nav_btn("🔄 My Borrows / Return", self.render_borrows_view).pack(fill="x")
        make_nav_btn("📊 SQC Quality Charts", self.render_sqc_view).pack(fill="x")

        if self.current_user["role"] == "admin":
            tk.Label(sidebar, text="ADMIN TOOLS", font=("Helvetica", 9, "bold"), bg=sidebar_bg, fg="#64748b").pack(anchor="w", padx=16, pady=(16, 8))
            make_nav_btn("➕ Add New Book", self.render_add_book_view).pack(fill="x")
            make_nav_btn("🛡️ Audit Trail (Q04)", self.render_audit_view).pack(fill="x")

        # Initial view
        self.render_catalog_view()

    def logout(self):
        log_audit_trail(self.current_user["username"], "LOGOUT", "User logged out.")
        self.current_user = None
        self.show_login_view()

    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # =========================================================================
    # VIEW: BOOK CATALOG
    # =========================================================================
    def render_catalog_view(self):
        self.clear_content()

        bg = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"

        # Search Controls Bar
        control_frame = tk.Frame(self.content_area, bg=card_bg, padx=12, pady=10)
        control_frame.pack(fill="x", pady=(0, 10))

        tk.Label(control_frame, text="Search Catalog:", font=("Helvetica", 10, "bold"), bg=card_bg, fg=fg).pack(side="left", padx=(0, 8))

        search_entry = tk.Entry(control_frame, font=("Helvetica", 10), width=28)
        search_entry.pack(side="left", padx=(0, 10))

        # Category Filter
        tk.Label(control_frame, text="Category:", font=("Helvetica", 9), bg=card_bg, fg=fg).pack(side="left", padx=(5, 4))
        categories = ["All"] + get_all_categories()
        cat_var = tk.StringVar(value="All")
        cat_menu = ttk.Combobox(control_frame, textvariable=cat_var, values=categories, state="readonly", width=16)
        cat_menu.pack(side="left", padx=(0, 10))

        # Latency metric badge
        latency_label = tk.Label(control_frame, text="", font=("Helvetica", 9), bg=card_bg, fg="#38bdf8")
        latency_label.pack(side="right", padx=10)

        # Books Table Treeview
        table_frame = tk.Frame(self.content_area, bg=bg)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "author", "isbn", "category", "copies")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("id", text="ID")
        tree.heading("title", text="Title")
        tree.heading("author", text="Author")
        tree.heading("isbn", text="ISBN")
        tree.heading("category", text="Category")
        tree.heading("copies", text="Available / Total")

        tree.column("id", width=40, anchor="center")
        tree.column("title", width=260)
        tree.column("author", width=180)
        tree.column("isbn", width=130)
        tree.column("category", width=140)
        tree.column("copies", width=110, anchor="center")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        def populate_catalog():
            for item in tree.get_children():
                tree.delete(item)
            books, latency_ms = search_books(query=search_entry.get(), category=cat_var.get())
            latency_label.config(text=f"⚡ Search Latency: {latency_ms:.2f} ms")
            for b in books:
                tree.insert(
                    "", "end",
                    values=(
                        b["id"], b["title"], b["author"], b["isbn"],
                        b["category"], f"{b['available_copies']} / {b['total_copies']}"
                    )
                )

        search_btn = tk.Button(control_frame, text="🔍 Search", bg="#2563eb", fg="#ffffff", font=("Helvetica", 9, "bold"),
                               cursor="hand2", command=populate_catalog)
        search_btn.pack(side="left", padx=4)

        search_entry.bind("<Return>", lambda event: populate_catalog())
        cat_menu.bind("<<ComboboxSelected>>", lambda event: populate_catalog())

        # Action Bar (Issue book)
        action_bar = tk.Frame(self.content_area, bg=bg, pady=8)
        action_bar.pack(fill="x")

        def handle_issue():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Notice", "Please select a book from the table to issue.")
                return

            book_values = tree.item(selected[0], "values")
            book_id = int(book_values[0])
            book_title = book_values[1]

            try:
                result = issue_book(
                    book_id=book_id,
                    user_id=self.current_user["id"],
                    username=self.current_user["username"]
                )
                messagebox.showinfo("Success", f"'{book_title}' has been successfully issued to you!\nDue Date: {result['due_date']}")
                populate_catalog()
            except ValidationError as err:
                messagebox.showerror("Error", str(err))

        tk.Button(
            action_bar, text="📥 Issue Selected Book to Me", font=("Helvetica", 10, "bold"),
            bg="#16a34a", fg="#ffffff", bd=0, padx=14, pady=6, cursor="hand2", command=handle_issue
        ).pack(side="left")

        populate_catalog()

    # =========================================================================
    # VIEW: BORROW RECORDS & RETURNS
    # =========================================================================
    def render_borrows_view(self):
        self.clear_content()

        bg = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"

        header_frame = tk.Frame(self.content_area, bg=card_bg, padx=12, pady=10)
        header_frame.pack(fill="x", pady=(0, 10))

        title = "My Borrowed Books & Returns" if self.current_user["role"] == "student" else "All System Borrow Records"
        tk.Label(header_frame, text=title, font=("Helvetica", 12, "bold"), bg=card_bg, fg=fg).pack(side="left")

        # Table
        table_frame = tk.Frame(self.content_area, bg=bg)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "user", "book_title", "borrow_date", "due_date", "return_date", "status", "fine")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("id", text="Record ID")
        tree.heading("user", text="User")
        tree.heading("book_title", text="Book Title")
        tree.heading("borrow_date", text="Borrow Date")
        tree.heading("due_date", text="Due Date")
        tree.heading("return_date", text="Return Date")
        tree.heading("status", text="Status")
        tree.heading("fine", text="Fine ($)")

        tree.column("id", width=65, anchor="center")
        tree.column("user", width=95)
        tree.column("book_title", width=220)
        tree.column("borrow_date", width=125)
        tree.column("due_date", width=125)
        tree.column("return_date", width=125)
        tree.column("status", width=90, anchor="center")
        tree.column("fine", width=70, anchor="center")

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        def populate_records():
            for item in tree.get_children():
                tree.delete(item)
            user_id = None if self.current_user["role"] == "admin" else self.current_user["id"]
            records = get_borrow_records(user_id=user_id)
            for r in records:
                tree.insert(
                    "", "end",
                    values=(
                        r["id"], r["username"], r["title"],
                        (r["borrow_date"] or "")[:10],
                        (r["due_date"] or "")[:10],
                        (r["return_date"] or "—")[:10],
                        r["status"],
                        f"${r['fine_amount']:.2f}"
                    )
                )

        populate_records()

        # Action: Return Book
        action_bar = tk.Frame(self.content_area, bg=bg, pady=8)
        action_bar.pack(fill="x")

        def handle_return():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Notice", "Please select a record from the list to return.")
                return

            vals = tree.item(selected[0], "values")
            record_id = int(vals[0])
            status = vals[6]

            if status != "BORROWED":
                messagebox.showinfo("Info", "This book is already marked as RETURNED.")
                return

            try:
                res = return_book(record_id, self.current_user["username"])
                msg = f"Book '{res['title']}' returned successfully!"
                if res['fine'] > 0:
                    msg += f"\nOverdue Late Fine: ${res['fine']:.2f}"
                messagebox.showinfo("Success", msg)
                populate_records()
            except ValidationError as err:
                messagebox.showerror("Error", str(err))

        tk.Button(
            action_bar, text="📤 Return Selected Book", font=("Helvetica", 10, "bold"),
            bg="#2563eb", fg="#ffffff", bd=0, padx=14, pady=6, cursor="hand2", command=handle_return
        ).pack(side="left")

    # =========================================================================
    # VIEW: SQC QUALITY ANALYSIS (TQM Q04)
    # =========================================================================
    def render_sqc_view(self):
        self.clear_content()

        bg = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"
        subtext = "#94a3b8"

        # Overview Header
        header = tk.Frame(self.content_area, bg=card_bg, padx=16, pady=10)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header, text="Statistical Quality Control (SQC) — Process Optimization (Q04)",
            font=("Helvetica", 13, "bold"), bg=card_bg, fg=fg
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Control chart tracking catalog search latency against Upper & Lower Control Limits (UCL / LCL = Mean ± 3σ).",
            font=("Helvetica", 9), bg=card_bg, fg=subtext
        ).pack(anchor="w", pady=(2, 0))

        # Metrics stats cards
        stats_frame = tk.Frame(self.content_area, bg=bg)
        stats_frame.pack(fill="x", pady=(0, 10))

        fig, stats = generate_sqc_chart(limit=35)

        cards_data = [
            ("Sample Size (N)", str(stats["count"]), "#38bdf8"),
            ("Process Mean (x̄)", f"{stats['mean']:.2f} ms", "#2ecc71"),
            ("Std Deviation (σ)", f"{stats['std']:.2f} ms", "#a855f7"),
            ("UCL (+3σ)", f"{stats['ucl']:.2f} ms", "#e74c3c"),
            ("LCL (-3σ)", f"{stats['lcl']:.2f} ms", "#3498db"),
            ("Out of Control", str(stats["out_of_control_count"]), "#22c55e" if stats["out_of_control_count"] == 0 else "#ef4444")
        ]

        for title, val, color in cards_data:
            c = tk.Frame(stats_frame, bg=card_bg, padx=10, pady=8, relief="ridge", bd=1)
            c.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(c, text=title, font=("Helvetica", 8), bg=card_bg, fg=subtext).pack()
            tk.Label(c, text=val, font=("Helvetica", 11, "bold"), bg=card_bg, fg=color).pack(pady=(2, 0))

        # Embed Matplotlib Figure into Tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        chart_frame = tk.Frame(self.content_area, bg=card_bg)
        chart_frame.pack(fill="both", expand=True)

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # =========================================================================
    # VIEW: ADD BOOK (ADMIN ONLY)
    # =========================================================================
    def render_add_book_view(self):
        self.clear_content()

        bg = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"

        card = tk.Frame(self.content_area, bg=card_bg, padx=30, pady=25)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Add New Book to Catalog", font=("Helvetica", 14, "bold"), bg=card_bg, fg=fg).pack(anchor="w", pady=(0, 15))

        fields = [
            ("Book Title", "title"),
            ("Author", "author"),
            ("ISBN (Unique)", "isbn"),
            ("Category", "category"),
            ("Total Copies", "copies")
        ]

        entries = {}
        for label_text, key in fields:
            tk.Label(card, text=label_text, font=("Helvetica", 10, "bold"), bg=card_bg, fg=fg).pack(anchor="w", pady=(6, 2))
            ent = tk.Entry(card, font=("Helvetica", 10), width=45)
            ent.pack(anchor="w", pady=(0, 6))
            entries[key] = ent

        entries["copies"].insert(0, "3")

        status_lbl = tk.Label(card, text="", font=("Helvetica", 9), bg=card_bg, fg="#e74c3c")
        status_lbl.pack(anchor="w", pady=6)

        def submit_book():
            try:
                copies_num = int(entries["copies"].get().strip())
                add_book(
                    title=entries["title"].get(),
                    author=entries["author"].get(),
                    isbn=entries["isbn"].get(),
                    category=entries["category"].get(),
                    copies=copies_num,
                    admin_user=self.current_user["username"]
                )
                messagebox.showinfo("Success", f"Book '{entries['title'].get()}' added to catalog successfully!")
                self.render_catalog_view()
            except ValueError:
                status_lbl.config(text="Total copies must be a valid integer number.")
            except ValidationError as err:
                status_lbl.config(text=str(err))

        tk.Button(
            card, text="Add Book", font=("Helvetica", 11, "bold"),
            bg="#2563eb", fg="#ffffff", padx=16, pady=6, cursor="hand2", command=submit_book
        ).pack(anchor="w", pady=(10, 0))

    # =========================================================================
    # VIEW: AUDIT TRAIL (ADMIN ONLY - Q04)
    # =========================================================================
    def render_audit_view(self):
        self.clear_content()

        bg = "#1e222d" if CTK_AVAILABLE else "#f0f2f5"
        card_bg = "#262b38" if CTK_AVAILABLE else "#ffffff"
        fg = "#ffffff" if CTK_AVAILABLE else "#1a202c"

        header_frame = tk.Frame(self.content_area, bg=card_bg, padx=12, pady=10)
        header_frame.pack(fill="x", pady=(0, 10))

        tk.Label(header_frame, text="Security Audit Trail & Activity Log (Q04)", font=("Helvetica", 12, "bold"), bg=card_bg, fg=fg).pack(side="left")

        table_frame = tk.Frame(self.content_area, bg=bg)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "timestamp", "username", "action", "details")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("id", text="Log ID")
        tree.heading("timestamp", text="Timestamp")
        tree.heading("username", text="User")
        tree.heading("action", text="Action")
        tree.heading("details", text="Event Details")

        tree.column("id", width=60, anchor="center")
        tree.column("timestamp", width=140)
        tree.column("username", width=110)
        tree.column("action", width=160)
        tree.column("details", width=380)

        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        logs = get_audit_logs(limit=100)
        for log in logs:
            tree.insert(
                "", "end",
                values=(log["id"], log["timestamp"], log["username"], log["action"], log["details"])
            )


def run_cli_fallback():
    """Fallback interactive CLI if running on headless server or missing Tkinter."""
    print("=" * 68)
    print("  BBAT104 TQM Library Management System (CLI Mode)")
    print("=" * 68)
    init_db()

    while True:
        print("\n1. Search Book Catalog")
        print("2. Login & Test Issue / Return")
        print("3. View SQC Quality Stats")
        print("4. Exit")
        choice = input("\nSelect an option [1-4]: ").strip()

        if choice == "1":
            q = input("Search query (or press Enter for all): ")
            books, latency = search_books(q)
            print(f"\nFound {len(books)} books (Latency: {latency:.2f} ms):")
            for b in books:
                print(f" - [{b['id']}] {b['title']} by {b['author']} (ISBN: {b['isbn']}) | Copies: {b['available_copies']}/{b['total_copies']}")
        elif choice == "2":
            u = input("Username (e.g. student1 or admin): ")
            p = input("Password: ")
            user = authenticate_user(u, p)
            if user:
                print(f"\nWelcome {user['full_name']} ({user['role']})!")
                if user['role'] == 'admin':
                    logs = get_audit_logs(5)
                    print("\nRecent Audit Logs:")
                    for l in logs:
                        print(f"  [{l['timestamp']}] {l['username']}: {l['action']} - {l['details']}")
            else:
                print("Login failed.")
        elif choice == "3":
            fig, stats = generate_sqc_chart()
            print("\n--- SQC Control Chart Metrics (Q04) ---")
            for k, v in stats.items():
                print(f"  {k}: {v}")
        elif choice == "4":
            print("Exiting.")
            break


def main():
    init_db()

    if not TK_AVAILABLE:
        print("\n" + "=" * 72)
        print("[!] NOTICE: Tkinter is not installed on this Python installation.")
        print("    To launch the full graphical desktop window, please run:")
        print("        sudo apt update && sudo apt install -y python3-tk")
        print("=" * 72 + "\n")
        run_cli_fallback()
        return

    # Check for graphical display
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        print("[!] No display found. Running in CLI mode.")
        run_cli_fallback()
        return

    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
