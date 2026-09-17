from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from equipment_system.models.equipment import Equipment, EquipmentState, EquipmentType
from equipment_system.models.operation_result import OperationResult
from equipment_system.services.equipment_service import EquipmentLoanSystem


class EquipmentApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Equipment Loan Management System")
        self.geometry("1366x768")
        self.minsize(1200, 700)
        self.service = EquipmentLoanSystem(capacity_k=5, hours_limit=8)
        self._build_ui()
        self._load_example_data()

    def _build_ui(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.inventory_tab = ttk.Frame(self.notebook)
        self.loan_tab = ttk.Frame(self.notebook)
        self.cart_tab = ttk.Frame(self.notebook)
        self.review_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.inventory_tab, text="Inventory")
        self.notebook.add(self.loan_tab, text="Loan Counter")
        self.notebook.add(self.cart_tab, text="Carts")
        self.notebook.add(self.review_tab, text="Review & Reports")

        self._build_inventory_tab()
        self._build_loan_tab()
        self._build_cart_tab()
        self._build_review_tab()

    def _build_inventory_tab(self) -> None:
        toolbar = ttk.Frame(self.inventory_tab)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(toolbar, text="Type:").pack(side="left")
        self.inventory_type_var = tk.StringVar(value="ALL")
        self.inventory_type_combo = ttk.Combobox(toolbar, textvariable=self.inventory_type_var, values=["ALL"] + EquipmentType.values(), state="readonly")
        self.inventory_type_combo.pack(side="left", padx=(5, 10))

        ttk.Label(toolbar, text="State:").pack(side="left")
        self.inventory_state_var = tk.StringVar(value="ALL")
        self.inventory_state_combo = ttk.Combobox(toolbar, textvariable=self.inventory_state_var, values=["ALL", *[state.value for state in EquipmentState]], state="readonly")
        self.inventory_state_combo.pack(side="left", padx=(5, 10))

        ttk.Button(toolbar, text="Apply Filters", command=self.refresh_inventory).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Clear", command=self.clear_inventory_filters).pack(side="left", padx=5)

        controls = ttk.Frame(self.inventory_tab)
        controls.pack(fill="x", padx=10, pady=5)

        ttk.Label(controls, text="Code").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.inventory_code_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.inventory_code_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(controls, text="Search", command=self.search_inventory_code).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(controls, text="Add Equipment", command=self.add_equipment).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(controls, text="Remove Equipment", command=self.remove_equipment).grid(row=0, column=4, padx=5, pady=5)

        self.inventory_tree = ttk.Treeview(self.inventory_tab, columns=("code", "type", "state", "loans", "student", "loan_start"), show="headings")
        self.inventory_tree.heading("code", text="Code")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("state", text="State")
        self.inventory_tree.heading("loans", text="Loans")
        self.inventory_tree.heading("student", text="Student")
        self.inventory_tree.heading("loan_start", text="Loan Start")
        for column in ("code", "type", "state", "loans", "student", "loan_start"):
            self.inventory_tree.column(column, width=120, anchor="center")
        self.inventory_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.inventory_message = tk.StringVar()
        ttk.Label(self.inventory_tab, textvariable=self.inventory_message, foreground="darkred").pack(anchor="w", padx=10, pady=(0, 10))

    def _build_loan_tab(self) -> None:
        frame = ttk.Frame(self.loan_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        form = ttk.LabelFrame(frame, text="Request / Return")
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Student").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.student_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.student_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Type").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.request_type_var = tk.StringVar(value=EquipmentType.PORTABLE.value)
        ttk.Combobox(form, textvariable=self.request_type_var, values=EquipmentType.values(), state="readonly").grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Minute").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.minute_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.minute_var, width=10).grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form, text="Request Equipment", command=self.request_equipment_action).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(form, text="Return Equipment", command=self.return_equipment_action).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="Manual Loan", command=self.manual_loan_action).grid(row=1, column=2, padx=5, pady=5)

        self.loan_message = tk.StringVar()
        ttk.Label(form, textvariable=self.loan_message, foreground="darkred").grid(row=1, column=3, columnspan=3, sticky="w", padx=5, pady=5)

        wait_frame = ttk.LabelFrame(frame, text="Waiting Queues")
        wait_frame.pack(fill="both", expand=True)

        self.waiting_labels = {}
        for idx, equipment_type in enumerate(EquipmentType):
            panel = ttk.LabelFrame(wait_frame, text=equipment_type.value)
            panel.grid(row=0, column=idx, padx=8, pady=8, sticky="nsew")
            ttk.Label(panel, text="FRONT").pack(anchor="w", padx=5, pady=(5, 0))
            label = ttk.Label(panel, text="-", foreground="darkblue", font=("TkDefaultFont", 10, "bold"))
            label.pack(anchor="w", padx=10)
            ttk.Label(panel, text="REAR").pack(anchor="w", padx=5, pady=(10, 0))
            rear_label = ttk.Label(panel, text="-", foreground="darkblue", font=("TkDefaultFont", 10, "bold"))
            rear_label.pack(anchor="w", padx=10)
            counter = ttk.Label(panel, text="0")
            counter.pack(anchor="w", padx=10, pady=(10, 10))
            self.waiting_labels[equipment_type.value] = {"front": label, "rear": rear_label, "count": counter}

    def _build_cart_tab(self) -> None:
        toolbar = ttk.Frame(self.cart_tab)
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(toolbar, text="Equipment Code").pack(side="left")
        self.directed_code_var = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.directed_code_var).pack(side="left", padx=(5, 10))
        ttk.Button(toolbar, text="Directed Loan", command=self.directed_loan_action).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Refresh Carts", command=self.refresh_carts).pack(side="left", padx=5)

        self.cart_panels = {}
        cart_area = ttk.Frame(self.cart_tab)
        cart_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        for idx, equipment_type in enumerate(EquipmentType):
            panel = ttk.LabelFrame(cart_area, text=equipment_type.value)
            panel.grid(row=0, column=idx, padx=8, pady=8, sticky="nsew")
            panel.grid_columnconfigure(0, weight=1)
            panel.grid_rowconfigure(0, weight=1)
            self.cart_panels[equipment_type.value] = panel

        self.directed_move_var = tk.StringVar(value="Pending")
        ttk.Label(self.cart_tab, textvariable=self.directed_move_var, foreground="darkgreen").pack(anchor="w", padx=10, pady=(0, 10))

    def _build_review_tab(self) -> None:
        review_frame = ttk.Frame(self.review_tab)
        review_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.LabelFrame(review_frame, text="Review Queue")
        left.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        right = ttk.LabelFrame(review_frame, text="Store Queue")
        right.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        metrics = ttk.LabelFrame(review_frame, text="Metrics")
        metrics.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")

        self.review_list = tk.Listbox(left, width=50, height=12)
        self.review_list.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(left, text="Approve", command=self.approve_review).pack(side="left", padx=5, pady=5)
        ttk.Button(left, text="Report Damage", command=self.damage_review).pack(side="left", padx=5, pady=5)

        self.store_list = tk.Listbox(right, width=50, height=12)
        self.store_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.metric_text = tk.Text(metrics, height=12, width=120)
        self.metric_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_list = tk.Listbox(self.review_tab, width=150, height=8)
        self.log_list.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(self.review_tab, text="Load Example Data", command=self._load_example_data).pack(anchor="w", padx=10, pady=(0, 10))

    def _load_example_data(self) -> None:
        sample = [
            {"code": "PORT-01", "type": "PORTABLE", "state": "IN_CART", "loans_count": 1},
            {"code": "PORT-02", "type": "PORTABLE", "state": "IN_CART", "loans_count": 0},
            {"code": "PORT-03", "type": "PORTABLE", "state": "IN_CART", "loans_count": 2},
            {"code": "KIT-01", "type": "KIT", "state": "IN_CART", "loans_count": 0},
            {"code": "KIT-02", "type": "KIT", "state": "IN_CART", "loans_count": 1},
            {"code": "MULT-01", "type": "MULTIMETER", "state": "IN_CART", "loans_count": 3},
            {"code": "MULT-02", "type": "MULTIMETER", "state": "IN_CART", "loans_count": 0},
        ]
        self.service.load_inventory(sample, capacity_k=5)
        self.refresh_all()

    def _show_message(self, target: tk.StringVar, text: str, is_error: bool = False) -> None:
        target.set(text)
        if is_error:
            target.set(text)

    def search_inventory_code(self) -> None:
        code = self.inventory_code_var.get().strip()
        result = self.service.search(code)
        if result.success:
            self._show_message(self.inventory_message, f"Equipment found: {result.data['equipment']['code']} / position {result.data['position_from_top']}")
        else:
            self._show_message(self.inventory_message, result.message, True)
        self.refresh_inventory()

    def add_equipment(self) -> None:
        code = self.inventory_code_var.get().strip()
        if not code:
            self._show_message(self.inventory_message, "Enter a valid equipment code.", True)
            return
        equipment_type = self.request_type_var.get() or EquipmentType.PORTABLE.value
        equipment = Equipment(code=code, equipment_type=EquipmentType.from_value(equipment_type))
        self.service.inventory.append(equipment)
        self.service._place_equipment_in_cart(equipment)
        self.refresh_all()
        self._show_message(self.inventory_message, f"Equipment {code} added.")

    def remove_equipment(self) -> None:
        code = self.inventory_code_var.get().strip()
        result = self.service.inventory.remove_by(lambda item: isinstance(item, Equipment) and item.code == code)
        if result is None:
            self._show_message(self.inventory_message, f"Equipment {code} not found.", True)
            return
        self._show_message(self.inventory_message, f"Equipment {code} removed.")
        self.refresh_all()

    def clear_inventory_filters(self) -> None:
        self.inventory_type_var.set("ALL")
        self.inventory_state_var.set("ALL")
        self.refresh_inventory()

    def refresh_inventory(self) -> None:
        items = self.service.get_inventory_snapshot()
        selected_type = self.inventory_type_var.get()
        selected_state = self.inventory_state_var.get()
        filtered = []
        for item in items:
            if selected_type != "ALL" and item["type"] != selected_type:
                continue
            if selected_state != "ALL" and item["state"] != selected_state:
                continue
            filtered.append(item)
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        for item in filtered:
            self.inventory_tree.insert("", "end", values=(
                item["code"],
                item["type"],
                item["state"],
                item["loans_count"],
                item["current_student"] or "-",
                item["loan_start_minute"] if item["loan_start_minute"] is not None else "-",
            ))

    def request_equipment_action(self) -> None:
        try:
            minute = int(self.minute_var.get())
        except ValueError:
            self._show_message(self.loan_message, "Minute must be an integer.", True)
            return
        student = self.student_var.get().strip()
        equipment_type = self.request_type_var.get()
        result = self.service.request_equipment(student, equipment_type, minute)
        self._show_message(self.loan_message, result.message if result.success else result.message, not result.success)
        self.refresh_all()

    def return_equipment_action(self) -> None:
        code = self.inventory_code_var.get().strip()
        try:
            minute = int(self.minute_var.get())
        except ValueError:
            self._show_message(self.loan_message, "Minute must be an integer.", True)
            return
        result = self.service.return_equipment(code, minute)
        self._show_message(self.loan_message, result.message if result.success else result.message, not result.success)
        self.refresh_all()

    def manual_loan_action(self) -> None:
        try:
            minute = int(self.minute_var.get())
        except ValueError:
            self._show_message(self.loan_message, "Minute must be an integer.", True)
            return
        result = self.service.lend(self.request_type_var.get(), self.student_var.get().strip(), minute)
        self._show_message(self.loan_message, result.message if result.success else result.message, not result.success)
        self.refresh_all()

    def refresh_waiting_queues(self) -> None:
        snapshot = self.service.get_waiting_snapshot()
        for equipment_type in EquipmentType:
            queue = snapshot.get(equipment_type.value, [])
            first = queue[0] if queue else {"student_code": "-"}
            last = queue[-1] if queue else {"student_code": "-"}
            self.waiting_labels[equipment_type.value]["front"].config(text=first.get("student_code", "-"))
            self.waiting_labels[equipment_type.value]["rear"].config(text=last.get("student_code", "-"))
            self.waiting_labels[equipment_type.value]["count"].config(text=str(len(queue)))

    def draw_cart_stack(self, equipment_type: EquipmentType, panel: ttk.LabelFrame) -> None:
        for widget in panel.winfo_children():
            widget.destroy()
        items = self.service.get_cart_snapshot().get(equipment_type.value, [])
        if not items:
            ttk.Label(panel, text="EMPTY", foreground="darkred").pack(padx=10, pady=20)
            return
        stack_label = ttk.Label(panel, text=f"Count: {len(items)}", font=("TkDefaultFont", 10, "bold"))
        stack_label.pack(pady=(8, 5))
        for item in reversed(items):
            cell = ttk.Label(panel, text=item, background="#e4f1ff", foreground="navy", borderwidth=1, relief="solid", padding=(10, 6))
            cell.pack(fill="x", padx=10, pady=2)
        ttk.Label(panel, text="TOP", foreground="darkgreen", font=("TkDefaultFont", 9, "bold")).pack(pady=(6, 10))

    def refresh_carts(self) -> None:
        for equipment_type in EquipmentType:
            self.draw_cart_stack(equipment_type, self.cart_panels[equipment_type.value])

    def directed_loan_action(self) -> None:
        code = self.directed_code_var.get().strip()
        student = self.student_var.get().strip() or "DIRECTED"
        minute = int(self.minute_var.get() or 0)
        result = self.service.lend_directed(code, student, minute)
        self.directed_move_var.set(f"Movement count: {result.data.get('movement_count', 0)}" if result.success else result.message)
        self.refresh_all()

    def refresh_review(self) -> None:
        review_items = self.service.get_review_snapshot()
        self.review_list.delete(0, tk.END)
        for item in review_items:
            self.review_list.insert(tk.END, f"{item['code']} | {item['state']}")
        store_items = self.service.get_store_snapshot()
        self.store_list.delete(0, tk.END)
        for item in store_items:
            self.store_list.insert(tk.END, f"{item['code']} | {item['type']}")
        report = self.service.report()
        self.metric_text.delete("1.0", tk.END)
        text = "\n".join(
            [
                f"Equipment by state: {report['equipment_by_state']}",
                f"Equipment by type: {report['equipment_by_type']}",
                f"Cart occupancy: {report['cart_occupancy']}",
                f"Immediate requests: {report['immediate_requests']}",
                f"Queued requests: {report['queued_requests']}",
                f"Average wait: {report['average_wait_minutes']} minutes",
                f"Directed loans: {report['directed_loans_count']} | total movements: {report['total_directed_movements']}",
                f"Damaged returns: {report['damaged_returns']} | maintenance: {report['equipment_in_maintenance']} | arrears: {report['equipment_in_arrears']}",
                f"Most borrowed: {report['most_borrowed_equipment']} | preventive maintenance: {report['preventive_maintenance_count']}",
            ]
        )
        self.metric_text.insert("1.0", text)
        self.log_list.delete(0, tk.END)
        for entry in self.service.get_logs():
            self.log_list.insert(tk.END, f"{entry['timestamp']}: {entry['message']}")

    def approve_review(self) -> None:
        if self.review_list.size() == 0:
            self._show_message(self.loan_message, "No review items to approve.", True)
            return
        result = self.service.review_next("APPROVE")
        self.refresh_all()
        self._show_message(self.loan_message, result.message if result.success else result.message, not result.success)

    def damage_review(self) -> None:
        if self.review_list.size() == 0:
            self._show_message(self.loan_message, "No review items to damage.", True)
            return
        result = self.service.review_next("DAMAGED")
        self.refresh_all()
        self._show_message(self.loan_message, result.message if result.success else result.message, not result.success)

    def refresh_all(self) -> None:
        self.refresh_inventory()
        self.refresh_waiting_queues()
        self.refresh_carts()
        self.refresh_review()


if __name__ == "__main__":
    app = EquipmentApp()
    app.mainloop()
