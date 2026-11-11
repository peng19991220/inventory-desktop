import os  
import sys  
import sqlite3  
import shutil  
import tkinter as tk  
from tkinter import ttk, messagebox, simpledialog, filedialog  
from datetime import datetime  
  
# ---------- 数据路径：exe 同目录 ----------  
if getattr(sys, 'frozen', False):  
    BASE_DIR = os.path.dirname(sys.executable)  
else:  
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
  
DATA_DIR = os.path.join(BASE_DIR, "data")  
BACKUP_DIR = os.path.join(BASE_DIR, "backup")  
os.makedirs(DATA_DIR, exist_ok=True)  
os.makedirs(BACKUP_DIR, exist_ok=True)  
DB_PATH = os.path.join(DATA_DIR, "inventory.db")  
  
def get_conn():  
    return sqlite3.connect(DB_PATH)  
  
def init_db():  
    conn = get_conn()  
    c = conn.cursor()  
    c.executescript("""  
    CREATE TABLE IF NOT EXISTS products (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        code TEXT UNIQUE,  
        name TEXT,  
        unit TEXT,  
        cost REAL,  
        price REAL,  
        stock INTEGER DEFAULT 0,  
        min_stock INTEGER DEFAULT 0  
    );  
    CREATE TABLE IF NOT EXISTS suppliers (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        name TEXT,  
        phone TEXT,  
        address TEXT  
    );  
    CREATE TABLE IF NOT EXISTS purchases (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        product_id INTEGER,  
        qty INTEGER,  
        price REAL,  
        total REAL,  
        supplier TEXT,  
        time TEXT DEFAULT (datetime('now','localtime'))  
    );  
    CREATE TABLE IF NOT EXISTS sales (  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        product_id INTEGER,  
        qty INTEGER,  
        price REAL,  
        total REAL,  
        customer TEXT,  
        time TEXT DEFAULT (datetime('now','localtime'))  
    );  
    CREATE TABLE IF NOT EXISTS users (  
        username TEXT PRIMARY KEY,  
        password TEXT  
    );  
    """)  
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin123')")  
    conn.commit()  
    conn.close()  
  
init_db()  
  
# ========== 主窗口 ==========  
class App:  
    def __init__(self, root):  
        self.root = root  
        self.root.title("进销存管理系统 v1.0")  
        self.root.geometry("1000x650")  
        self.root.minsize(800, 500)  
  
        # 菜单栏  
        menubar = tk.Menu(self.root)  
        self.root.config(menu=menubar)  
  
        sys_menu = tk.Menu(menubar, tearoff=0)  
        sys_menu.add_command(label="数据备份", command=self.backup_data)  
        sys_menu.add_command(label="数据恢复", command=self.restore_data)  
        sys_menu.add_separator()  
        sys_menu.add_command(label="修改密码", command=self.change_pwd)  
        sys_menu.add_separator()  
        sys_menu.add_command(label="退出", command=self.root.quit)  
        menubar.add_cascade(label="系统", menu=sys_menu)  
  
        help_menu = tk.Menu(menubar, tearoff=0)  
        help_menu.add_command(label="关于", command=lambda: messagebox.showinfo("关于", "进销存管理系统 v1.0\n单机版·SQLite本地存储"))  
        menubar.add_cascade(label="帮助", menu=help_menu)  
  
        # 工具栏  
        toolbar = tk.Frame(self.root, bg="#f0f0f0", height=40)  
        toolbar.pack(side=tk.TOP, fill=tk.X)  
  
        btn_style = {"padx": 10, "pady": 2, "bg": "#4a7db4", "fg": "white", "bd": 0}  
        tk.Button(toolbar, text="📦 商品管理", command=self.show_products, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Button(toolbar, text="📥 采购入库", command=self.show_purchases, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Button(toolbar, text="📤 销售出库", command=self.show_sales, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Button(toolbar, text="📋 库存查询", command=self.show_stock, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Button(toolbar, text="⚠️ 库存预警", command=self.show_warning, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
        tk.Button(toolbar, text="📊 报表统计", command=self.show_report, **btn_style).pack(side=tk.LEFT, padx=5, pady=5)  
  
        # 主内容区  
        self.main_frame = tk.Frame(self.root)  
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)  
  
        # 状态栏  
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)  
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)  
  
        # 默认显示仪表盘  
        self.show_dashboard()  
  
    def clear_main(self):  
        for w in self.main_frame.winfo_children():  
            w.destroy()  
  
    def set_status(self, msg):  
        self.status_bar.config(text=msg)  
  
    # ========== 仪表盘 ==========  
    def show_dashboard(self):  
        self.clear_main()  
        conn = get_conn()  
        p_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]  
        p_stock = conn.execute("SELECT SUM(stock) FROM products").fetchone()[0] or 0  
        p_value = conn.execute("SELECT SUM(stock*cost) FROM products").fetchone()[0] or 0  
        warning_count = conn.execute("SELECT COUNT(*) FROM products WHERE stock<=min_stock AND min_stock>0").fetchone()[0]  
        conn.close()  
  
        tk.Label(self.main_frame, text="📊 系统概览", font=("微软雅黑", 18, "bold")).pack(pady=10)  
  
        info_frame = tk.Frame(self.main_frame)  
        info_frame.pack(pady=20)  
  
        cards = [  
            ("商品种类", f"{p_count} 种"),  
            ("总库存量", f"{p_stock}"),  
            ("库存价值", f"¥{p_value:.2f}"),  
            ("库存预警", f"{warning_count} 项"),  
        ]  
        for i, (title, val) in enumerate(cards):  
            card = tk.Frame(info_frame, bg="#e8f4f8", bd=1, relief=tk.RIDGE, width=180, height=100)  
            card.grid(row=0, column=i, padx=10, pady=10)  
            card.pack_propagate(False)  
            tk.Label(card, text=title, bg="#e8f4f8", font=("微软雅黑", 10)).pack(pady=(15, 5))  
            tk.Label(card, text=val, bg="#e8f4f8", font=("微软雅黑", 16, "bold"), fg="#2a6d9c").pack()  
  
        tk.Label(self.main_frame, text="💡 提示：使用上方工具栏进入各功能模块", fg="gray").pack(pady=20)  
  
    # ========== 商品管理 ==========  
    def show_products(self):  
        self.clear_main()  
        self.set_status("商品管理")  
  
        tk.Label(self.main_frame, text="📦 商品管理", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        # 搜索框  
        search_frame = tk.Frame(self.main_frame)  
        search_frame.pack(fill=tk.X, pady=5)  
        tk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)  
        self.prod_search_var = tk.StringVar()  
        tk.Entry(search_frame, textvariable=self.prod_search_var, width=30).pack(side=tk.LEFT, padx=5)  
        tk.Button(search_frame, text="搜索", command=self.refresh_products).pack(side=tk.LEFT, padx=5)  
        tk.Button(search_frame, text="添加商品", command=self.add_product_dialog, bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)  
  
        # 表格  
        columns = ("编号", "商品编码", "名称", "单位", "进价", "售价", "库存", "最低库存")  
        self.prod_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=18)  
        for col in columns:  
            self.prod_tree.heading(col, text=col)  
            self.prod_tree.column(col, width=100)  
        self.prod_tree.column("编号", width=50)  
        self.prod_tree.pack(fill=tk.BOTH, expand=True, pady=5)  
  
        # 右键菜单  
        prod_menu = tk.Menu(self.main_frame, tearoff=0)  
        prod_menu.add_command(label="编辑", command=self.edit_product_dialog)  
        prod_menu.add_command(label="删除", command=self.delete_product)  
        self.prod_tree.bind("<Button-3>", lambda e: prod_menu.post(e.x_root, e.y_root))  
  
        self.refresh_products()  
  
    def refresh_products(self):  
        for row in self.prod_tree.get_children():  
            self.prod_tree.delete(row)  
        kw = self.prod_search_var.get().strip()  
        conn = get_conn()  
        if kw:  
            rows = conn.execute("SELECT * FROM products WHERE name LIKE ? OR code LIKE ?", (f"%{kw}%", f"%{kw}%")).fetchall()  
        else:  
            rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()  
        conn.close()  
        for r in rows:  
            self.prod_tree.insert("", tk.END, values=r)  
  
    def add_product_dialog(self):  
        dlg = tk.Toplevel(self.root)  
        dlg.title("添加商品")  
        dlg.geometry("350x300")  
        dlg.resizable(False, False)  
  
        fields = [("商品编码", "code"), ("名称", "name"), ("单位", "unit"), ("进价", "cost"), ("售价", "price"), ("初始库存", "stock"), ("最低库存", "min_stock")]  
        entries = {}  
        for i, (label, key) in enumerate(fields):  
            tk.Label(dlg, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)  
            e = tk.Entry(dlg, width=25)  
            e.grid(row=i, column=1, padx=10, pady=5)  
            entries[key] = e  
  
        def save():  
            try:  
                conn = get_conn()  
                conn.execute("INSERT INTO products (code,name,unit,cost,price,stock,min_stock) VALUES (?,?,?,?,?,?,?)",  
                             (entries["code"].get(), entries["name"].get(), entries["unit"].get(),  
                              float(entries["cost"].get() or 0), float(entries["price"].get() or 0),  
                              int(entries["stock"].get() or 0), int(entries["min_stock"].get() or 0)))  
                conn.commit()  
                conn.close()  
                self.refresh_products()  
                dlg.destroy()  
                self.set_status("商品添加成功")  
            except Exception as ex:  
                messagebox.showerror("错误", str(ex))  
  
        tk.Button(dlg, text="保存", command=save, bg="#4CAF50", fg="white", width=10).grid(row=len(fields), column=0, columnspan=2, pady=15)  
  
    def edit_product_dialog(self):  
        sel = self.prod_tree.selection()  
        if not sel:  
            messagebox.showwarning("提示", "请先选择要编辑的商品")  
            return  
        vals = self.prod_tree.item(sel[0], "values")  
        dlg = tk.Toplevel(self.root)  
        dlg.title("编辑商品")  
        dlg.geometry("350x300")  
        dlg.resizable(False, False)  
  
        fields = [("商品编码", "code"), ("名称", "name"), ("单位", "unit"), ("进价", "cost"), ("售价", "price"), ("库存", "stock"), ("最低库存", "min_stock")]  
        entries = {}  
        for i, (label, key) in enumerate(fields):  
            tk.Label(dlg, text=label).grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)  
            e = tk.Entry(dlg, width=25)  
            e.grid(row=i, column=1, padx=10, pady=5)  
            e.insert(0, vals[i+1] if i < len(vals)-1 else "")  
            entries[key] = e  
  
        def save():  
            try:  
                conn = get_conn()  
                conn.execute("UPDATE products SET code=?,name=?,unit=?,cost=?,price=?,stock=?,min_stock=? WHERE id=?",  
                             (entries["code"].get(), entries["name"].get(), entries["unit"].get(),  
                              float(entries["cost"].get() or 0), float(entries["price"].get() or 0),  
                              int(entries["stock"].get() or 0), int(entries["min_stock"].get() or 0), int(vals[0])))  
                conn.commit()  
                conn.close()  
                self.refresh_products()  
                dlg.destroy()  
                self.set_status("商品更新成功")  
            except Exception as ex:  
                messagebox.showerror("错误", str(ex))  
  
        tk.Button(dlg, text="保存", command=save, bg="#4CAF50", fg="white", width=10).grid(row=len(fields), column=0, columnspan=2, pady=15)  
  
    def delete_product(self):  
        sel = self.prod_tree.selection()  
        if not sel:  
            return  
        if not messagebox.askyesno("确认", "确定删除该商品？"):  
            return  
        pid = self.prod_tree.item(sel[0], "values")[0]  
        conn = get_conn()  
        conn.execute("DELETE FROM products WHERE id=?", (pid,))  
        conn.commit()  
        conn.close()  
        self.refresh_products()  
        self.set_status("商品已删除")  
  
    # ========== 采购入库 ==========  
    def show_purchases(self):  
        self.clear_main()  
        self.set_status("采购入库")  
  
        tk.Label(self.main_frame, text="📥 采购入库", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        # 入库表单  
        form = tk.Frame(self.main_frame)  
        form.pack(fill=tk.X, pady=5)  
  
        tk.Label(form, text="商品：").grid(row=0, column=0, padx=5, pady=3)  
        self.pur_prod_var = tk.StringVar()  
        self.pur_prod_combo = ttk.Combobox(form, textvariable=self.pur_prod_var, width=25)  
        self.pur_prod_combo.grid(row=0, column=1, padx=5, pady=3)  
  
        tk.Label(form, text="数量：").grid(row=0, column=2, padx=5, pady=3)  
        self.pur_qty_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.pur_qty_var, width=10).grid(row=0, column=3, padx=5, pady=3)  
  
        tk.Label(form, text="单价：").grid(row=0, column=4, padx=5, pady=3)  
        self.pur_price_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.pur_price_var, width=10).grid(row=0, column=5, padx=5, pady=3)  
  
        tk.Label(form, text="供应商：").grid(row=0, column=6, padx=5, pady=3)  
        self.pur_sup_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.pur_sup_var, width=15).grid(row=0, column=7, padx=5, pady=3)  
  
        tk.Button(form, text="入库", command=self.do_purchase, bg="#2196F3", fg="white", width=8).grid(row=0, column=8, padx=10, pady=3)  
  
        # 刷新商品列表  
        conn = get_conn()  
        prods = conn.execute("SELECT id, name FROM products").fetchall()  
        conn.close()  
        self.pur_prod_combo["values"] = [f"{p[0]}-{p[1]}" for p in prods]  
  
        # 入库记录表  
        columns = ("编号", "商品", "数量", "单价", "总额", "供应商", "时间")  
        self.pur_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)  
        for col in columns:  
            self.pur_tree.heading(col, text=col)  
            self.pur_tree.column(col, width=120)  
        self.pur_tree.column("编号", width=50)  
        self.pur_tree.pack(fill=tk.BOTH, expand=True, pady=5)  
  
        self.refresh_purchases()  
  
    def do_purchase(self):  
        try:  
            sel = self.pur_prod_var.get()  
            pid = int(sel.split("-")[0])  
            qty = int(self.pur_qty_var.get())  
            price = float(self.pur_price_var.get())  
            total = qty * price  
            sup = self.pur_sup_var.get()  
  
            conn = get_conn()  
            conn.execute("INSERT INTO purchases (product_id,qty,price,total,supplier) VALUES (?,?,?,?,?)",  
                         (pid, qty, price, total, sup))  
            conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (qty, pid))  
            conn.commit()  
            conn.close()  
  
            self.pur_qty_var.set("")  
            self.pur_price_var.set("")  
            self.pur_sup_var.set("")  
            self.refresh_purchases()  
            self.set_status("入库成功")  
        except Exception as ex:  
            messagebox.showerror("错误", f"入库失败：{ex}")  
  
    def refresh_purchases(self):  
        for row in self.pur_tree.get_children():  
            self.pur_tree.delete(row)  
        conn = get_conn()  
        rows = conn.execute("""  
            SELECT p.id, pr.name, p.qty, p.price, p.total, p.supplier, p.time  
            FROM purchases p LEFT JOIN products pr ON p.product_id=pr.id  
            ORDER BY p.id DESC LIMIT 200  
        """).fetchall()  
        conn.close()  
        for r in rows:  
            self.pur_tree.insert("", tk.END, values=r)  
  
    # ========== 销售出库 ==========  
    def show_sales(self):  
        self.clear_main()  
        self.set_status("销售出库")  
  
        tk.Label(self.main_frame, text="📤 销售出库", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        form = tk.Frame(self.main_frame)  
        form.pack(fill=tk.X, pady=5)  
  
        tk.Label(form, text="商品：").grid(row=0, column=0, padx=5, pady=3)  
        self.sale_prod_var = tk.StringVar()  
        self.sale_prod_combo = ttk.Combobox(form, textvariable=self.sale_prod_var, width=25)  
        self.sale_prod_combo.grid(row=0, column=1, padx=5, pady=3)  
  
        tk.Label(form, text="数量：").grid(row=0, column=2, padx=5, pady=3)  
        self.sale_qty_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.sale_qty_var, width=10).grid(row=0, column=3, padx=5, pady=3)  
  
        tk.Label(form, text="单价：").grid(row=0, column=4, padx=5, pady=3)  
        self.sale_price_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.sale_price_var, width=10).grid(row=0, column=5, padx=5, pady=3)  
  
        tk.Label(form, text="客户：").grid(row=0, column=6, padx=5, pady=3)  
        self.sale_cust_var = tk.StringVar()  
        tk.Entry(form, textvariable=self.sale_cust_var, width=15).grid(row=0, column=7, padx=5, pady=3)  
  
        tk.Button(form, text="出库", command=self.do_sale, bg="#FF5722", fg="white", width=8).grid(row=0, column=8, padx=10, pady=3)  
  
        conn = get_conn()  
        prods = conn.execute("SELECT id, name FROM products").fetchall()  
        conn.close()  
        self.sale_prod_combo["values"] = [f"{p[0]}-{p[1]}" for p in prods]  
  
        columns = ("编号", "商品", "数量", "单价", "总额", "客户", "时间")  
        self.sale_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)  
        for col in columns:  
            self.sale_tree.heading(col, text=col)  
            self.sale_tree.column(col, width=120)  
        self.sale_tree.column("编号", width=50)  
        self.sale_tree.pack(fill=tk.BOTH, expand=True, pady=5)  
  
        self.refresh_sales()  
  
    def do_sale(self):  
        try:  
            sel = self.sale_prod_var.get()  
            pid = int(sel.split("-")[0])  
            qty = int(self.sale_qty_var.get())  
            price = float(self.sale_price_var.get())  
            total = qty * price  
            cust = self.sale_cust_var.get()  
  
            conn = get_conn()  
            cur_stock = conn.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()[0]  
            if cur_stock < qty:  
                messagebox.showerror("错误", f"库存不足！当前库存：{cur_stock}")  
                conn.close()  
                return  
            conn.execute("INSERT INTO sales (product_id,qty,price,total,customer) VALUES (?,?,?,?,?)",  
                         (pid, qty, price, total, cust))  
            conn.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, pid))  
            conn.commit()  
            conn.close()  
  
            self.sale_qty_var.set("")  
            self.sale_price_var.set("")  
            self.sale_cust_var.set("")  
            self.refresh_sales()  
            self.set_status("出库成功")  
        except Exception as ex:  
            messagebox.showerror("错误", f"出库失败：{ex}")  
  
    def refresh_sales(self):  
        for row in self.sale_tree.get_children():  
            self.sale_tree.delete(row)  
        conn = get_conn()  
        rows = conn.execute("""  
            SELECT s.id, pr.name, s.qty, s.price, s.total, s.customer, s.time  
            FROM sales s LEFT JOIN products pr ON s.product_id=pr.id  
            ORDER BY s.id DESC LIMIT 200  
        """).fetchall()  
        conn.close()  
        for r in rows:  
            self.sale_tree.insert("", tk.END, values=r)  
  
    # ========== 库存查询 ==========  
    def show_stock(self):  
        self.clear_main()  
        self.set_status("库存查询")  
  
        tk.Label(self.main_frame, text="📋 库存查询", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        search_frame = tk.Frame(self.main_frame)  
        search_frame.pack(fill=tk.X, pady=5)  
        tk.Label(search_frame, text="搜索：").pack(side=tk.LEFT)  
        self.stock_search_var = tk.StringVar()  
        tk.Entry(search_frame, textvariable=self.stock_search_var, width=30).pack(side=tk.LEFT, padx=5)  
        tk.Button(search_frame, text="查询", command=self.refresh_stock).pack(side=tk.LEFT, padx=5)  
  
        columns = ("编号", "编码", "名称", "单位", "进价", "售价", "库存", "库存价值", "最低库存")  
        self.stock_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=18)  
        for col in columns:  
            self.stock_tree.heading(col, text=col)  
            self.stock_tree.column(col, width=100)  
        self.stock_tree.column("编号", width=50)  
        self.stock_tree.pack(fill=tk.BOTH, expand=True, pady=5)  
  
        self.refresh_stock()  
  
    def refresh_stock(self):  
        for row in self.stock_tree.get_children():  
            self.stock_tree.delete(row)  
        kw = self.stock_search_var.get().strip()  
        conn = get_conn()  
        if kw:  
            rows = conn.execute("SELECT id,code,name,unit,cost,price,stock,stock*cost,min_stock FROM products WHERE name LIKE ? OR code LIKE ?",  
                                (f"%{kw}%", f"%{kw}%")).fetchall()  
        else:  
            rows = conn.execute("SELECT id,code,name,unit,cost,price,stock,stock*cost,min_stock FROM products ORDER BY id").fetchall()  
        conn.close()  
        for r in rows:  
            self.stock_tree.insert("", tk.END, values=r)  
  
    # ========== 库存预警 ==========  
    def show_warning(self):  
        self.clear_main()  
        self.set_status("库存预警")  
  
        tk.Label(self.main_frame, text="⚠️ 库存预警", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        columns = ("编号", "编码", "名称", "当前库存", "最低库存", "建议补货")  
        self.warn_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=18)  
        for col in columns:  
            self.warn_tree.heading(col, text=col)  
            self.warn_tree.column(col, width=120)  
        self.warn_tree.column("编号", width=50)  
        self.warn_tree.pack(fill=tk.BOTH, expand=True, pady=5)  
  
        conn = get_conn()  
        rows = conn.execute("""  
            SELECT id,code,name,stock,min_stock,min_stock-stock  
            FROM products WHERE stock<=min_stock AND min_stock>0  
            ORDER BY stock ASC  
        """).fetchall()  
        conn.close()  
  
        if not rows:  
            tk.Label(self.main_frame, text="✅ 所有商品库存正常，无需预警", fg="green", font=("微软雅黑", 12)).pack(pady=20)  
        else:  
            for r in rows:  
                self.warn_tree.insert("", tk.END, values=r)  
            tk.Label(self.main_frame, text=f"共 {len(rows)} 项商品库存不足，请及时补货", fg="red").pack()  
  
    # ========== 报表统计 ==========  
    def show_report(self):  
        self.clear_main()  
        self.set_status("报表统计")  
  
        tk.Label(self.main_frame, text="📊 报表统计", font=("微软雅黑", 16, "bold")).pack(anchor=tk.W, pady=5)  
  
        conn = get_conn()  
  
        # 今日销售  
        today = datetime.now().strftime("%Y-%m-%d")  
        today_sales = conn.execute("""  
            SELECT COUNT(*), COALESCE(SUM(total),0) FROM sales WHERE time LIKE ?  
        """, (f"{today}%",)).fetchone()  
  
        # 本月销售  
        month = datetime.now().strftime("%Y-%m")  
        month_sales = conn.execute("""  
            SELECT COUNT(*), COALESCE(SUM(total),0) FROM sales WHERE time LIKE ?  
        """, (f"{month}%",)).fetchone()  
  
        # 总采购  
        total_pur = conn.execute("SELECT COALESCE(SUM(total),0) FROM purchases").fetchone()[0]  
        total_sale = conn.execute("SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]  
  
        conn.close()  
  
        report_frame = tk.Frame(self.main_frame)  
        report_frame.pack(pady=20)  
  
        items = [  
            ("今日销售单数", f"{today_sales[0]} 单"),  
            ("今日销售额", f"¥{today_sales[1]:.2f}"),  
            ("本月销售单数", f"{month_sales[0]} 单"),  
            ("本月销售额", f"¥{month_sales[1]:.2f}"),  
            ("总采购金额", f"¥{total_pur:.2f}"),  
            ("总销售金额", f"¥{total_sale:.2f}"),  
            ("毛利", f"¥{total_sale - total_pur:.2f}"),  
        ]  
  
        for i, (label, val) in enumerate(items):  
            row = i // 3  
            col = i % 3  
            card = tk.Frame(report_frame, bg="#fff3e0", bd=1, relief=tk.RIDGE, width=200, height=80)  
            card.grid(row=row, column=col, padx=10, pady=10)  
            card.pack_propagate(False)  
            tk.Label(card, text=label, bg="#fff3e0", font=("微软雅黑", 10)).pack(pady=(10, 2))  
            tk.Label(card, text=val, bg="#fff3e0", font=("微软雅黑", 14, "bold"), fg="#e65100").pack()  
  
    # ========== 备份与恢复 ==========  
    def backup_data(self):  
        try:  
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")  
            backup_file = os.path.join(BACKUP_DIR, f"inventory_backup_{ts}.db")  
            shutil.copy2(DB_PATH, backup_file)  
            messagebox.showinfo("成功", f"数据已备份到：\n{backup_file}")  
            self.set_status(f"备份成功：{backup_file}")  
        except Exception as ex:  
            messagebox.showerror("错误", f"备份失败：{ex}")  
  
    def restore_data(self):  
        files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]  
        if not files:  
            messagebox.showinfo("提示", "没有找到备份文件")  
            return  
        dlg = tk.Toplevel(self.root)  
        dlg.title("选择备份文件")  
        dlg.geometry("400x300")  
        tk.Label(dlg, text="选择要恢复的备份文件：").pack(pady=10)  
        lb = tk.Listbox(dlg, width=60, height=12)  
        lb.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)  
        for f in files:  
            lb.insert(tk.END, f)  
  
        def do_restore():  
            sel = lb.curselection()  
            if not sel:  
                return  
            fname = lb.get(sel[0])  
            src = os.path.join(BACKUP_DIR, fname)  
            if messagebox.askyesno("确认", f"恢复后当前数据将被覆盖，确定恢复？"):  
                shutil.copy2(src, DB_PATH)  
                messagebox.showinfo("成功", "数据恢复成功，请重启程序")  
                dlg.destroy()  
                self.set_status("数据已恢复")  
  
        tk.Button(dlg, text="恢复", command=do_restore, bg="#FF9800", fg="white", width=10).pack(pady=10)  
  
    # ========== 修改密码 ==========  
    def change_pwd(self):  
        dlg = tk.Toplevel(self.root)  
        dlg.title("修改密码")  
        dlg.geometry("300x180")  
        dlg.resizable(False, False)  
  
        tk.Label(dlg, text="当前密码：").pack(pady=5)  
        old_var = tk.StringVar()  
        tk.Entry(dlg, textvariable=old_var, show="*", width=25).pack()  
  
        tk.Label(dlg, text="新密码：").pack(pady=5)  
        new_var = tk.StringVar()  
        tk.Entry(dlg, textvariable=new_var, show="*", width=25).pack()  
  
        def save():  
            conn = get_conn()  
            row = conn.execute("SELECT password FROM users WHERE username='admin'").fetchone()  
            if row and row[0] == old_var.get():  
                conn.execute("UPDATE users SET password=? WHERE username='admin'", (new_var.get(),))  
                conn.commit()  
                conn.close()  
                messagebox.showinfo("成功", "密码已修改")  
                dlg.destroy()  
            else:  
                conn.close()  
                messagebox.showerror("错误", "当前密码不正确")  
  
        tk.Button(dlg, text="确认修改", command=save, bg="#4CAF50", fg="white", width=12).pack(pady=15)  
  
# ========== 启动 ==========  
if __name__ == "__main__":  
    root = tk.Tk()  
    app = App(root)  
    root.mainloop()  
