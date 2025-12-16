import os
from myserver import server_on
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import datetime
from discord.ui import Button, View, Modal, InputText
# --- การตั้งค่าเบื้องต้น ---
API_URL = 'https://your-website.com/api' # URL เว็บของคุณ
API_KEY = 'YOUR_SECRET_API_KEY' # คีย์สำหรับความปลอดภัย
ADMIN_CHANNEL_ID = 11449323389297758252  # ห้องหลังบ้าน
MAIN_CHANNEL_ID = 1441450446339854041119   # ห้องหน้าเติมเงิน
class ShopBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Synced commands successfully.")

    async def on_ready(self):
        print(f'Logged in as {self.user}!')

bot = ShopBot()

# --- ส่วนจำลองการเชื่อมต่อ API (Mock API Functions) ---
# ในการใช้งานจริง ให้ใช้ aiohttp เพื่อยิง Request ไปยังเว็บของคุณ
async def fetch_products():
    # ตัวอย่าง: ดึงรายการสินค้าจาก API
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(f"{API_URL}/products") as resp:
    #         return await resp.json()
    
    # จำลองข้อมูลส่งกลับมา
    return [
        {"id": "p1", "name": "Youtube Premium (1 เดือน)", "price": 50, "stock": 10},
        {"id": "p2", "name": "Netflix 4K (1 จอ)", "price": 120, "stock": 5},
        {"id": "p3", "name": "Spotify Premium", "price": 30, "stock": 0}, # ของหมด
    ]

async def get_user_balance(user_id):
    # ดึงยอดเงินคงเหลือของผู้ใช้
    return 150.00 # สมมติว่ามีเงิน 150 บาท

async def process_purchase(user_id, product_id):
    # ส่งข้อมูลการซื้อไปที่เว็บ
    return {"status": "success", "code": "X99-KEY-PREMIUM-CODE", "message": "ซื้อสำเร็จ!"}

# --- UI Components (เมนูและปุ่มต่างๆ) ---

class PaymentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ธนาคาร (Bank)", style=discord.ButtonStyle.primary, emoji="🏦")
    async def bank_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="💳 ช่องทางการชำระเงิน: ธนาคาร", color=discord.Color.blue())
        embed.add_field(name="ธนาคาร", value="กสิกรไทย (KBank)", inline=False)
        embed.add_field(name="เลขบัญชี", value="123-4-56789-0", inline=False)
        embed.add_field(name="ชื่อบัญชี", value="นายทดสอบ ระบบบอท", inline=False)
        embed.set_footer(text="เมื่อโอนแล้วกรุณาแจ้งสลิปในเมนูแจ้งเติมเงิน")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="TrueMoney Wallet", style=discord.ButtonStyle.danger, emoji="🧧")
    async def wallet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🧧 ช่องทางการชำระเงิน: TrueMoney Wallet", color=discord.Color.orange())
        embed.add_field(name="เบอร์วอลเลท", value="081-234-5678", inline=False)
        embed.add_field(name="ชื่อบัญชี", value="นายทดสอบ ระบบบอท", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ProductSelect(discord.ui.Select):
    def __init__(self, products):
        options = []
        for p in products:
            status = "✅" if p['stock'] > 0 else "❌ หมด"
            options.append(discord.SelectOption(
                label=f"{p['name']} - {p['price']}฿",
                description=f"สถานะ: {status}",
                value=p['id']
            ))
        super().__init__(placeholder="🔻 เลือกสินค้าที่ต้องการซื้อ...", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        product_id = self.values[0]
        # ตรวจสอบยอดเงินและตัดสต็อก (เรียก API)
        result = await process_purchase(interaction.user.id, product_id)
        
        if result["status"] == "success":
            await interaction.response.send_message(
                f"✅ **ซื้อสำเร็จ!**\nสินค้าของคุณ: `{result['code']}`\n(ระบบได้ส่งข้อมูลเข้า DM แล้ว)",
                ephemeral=True
            )
            # ควรส่ง DM หา user ด้วยเพื่อความปลอดภัยของสินค้า
            try:
                await interaction.user.send(f"ขอบคุณที่สั่งซื้อ! นี่คือสินค้าของคุณ: {result['code']}")
            except:
                pass
        else:
            await interaction.response.send_message("❌ เกิดข้อผิดพลาด หรือยอดเงินไม่พอ", ephemeral=True)

class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 รายการสินค้า", style=discord.ButtonStyle.success, row=1)
    async def shop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = await fetch_products() # ดึงข้อมูลสดจาก API
        view = discord.ui.View()
        view.add_item(ProductSelect(products))
        await interaction.response.send_message("เลือกสินค้าด้านล่างได้เลยครับ:", view=view, ephemeral=True)

    @discord.ui.button(label="💰 เติมเงิน / เลขบัญชี", style=discord.ButtonStyle.secondary, row=1)
    async def topup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("เลือกช่องทางการโอนเงิน:", view=PaymentView(), ephemeral=True)

    @discord.ui.button(label="👤 ประวัติ & ข้อมูลส่วนตัว", style=discord.ButtonStyle.primary, row=2)
    async def profile_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        balance = await get_user_balance(interaction.user.id)
        embed = discord.Embed(title=f"ข้อมูลของ {interaction.user.name}", color=discord.Color.green())
        embed.add_field(name="💵 ยอดเงินคงเหลือ", value=f"{balance:.2f} บาท")
        embed.add_field(name="📜 ประวัติการซื้อ", value="กดเพื่อดูประวัติย้อนหลัง (API)", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📦 เช็คสต็อก", style=discord.ButtonStyle.secondary, row=2)
    async def stock_check(self, interaction: discord.Interaction, button: discord.ui.Button):
        products = await fetch_products()
        msg = "**📦 รายการสต็อกปัจจุบัน (Real-time):**\n"
        for p in products:
            msg += f"- {p['name']}: `{p['stock']}` ชิ้น\n"
        await interaction.response.send_message(msg, ephemeral=True)

# --- Slash Commands ---

@bot.tree.command(name="start", description="เปิดเมนูร้านค้า")
async def start(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 ยินดีต้อนรับสู่ Premium App Store",
        description="ระบบอัตโนมัติ 24 ชั่วโมง เลือกทำรายการได้ที่เมนูด้านล่าง",
        color=discord.Color.gold()
    )
    embed.set_image(url="https://via.placeholder.com/600x200?text=Shop+Banner") # ใส่รูปแบนเนอร์ร้าน
    await interaction.response.send_message(embed=embed, view=MainMenuView())

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- ส่วนจำลอง Database (ในใช้งานจริงควรเชื่อมต่อ MongoDB หรือ SQL) ---
shop_data = {
    "payment_number": "ยังไม่ระบุ",
    "products": {}  # รูปแบบ: {'Netflix': {'price': 100, 'stock': []}}
}

# --- Modal: หน้าต่างกรอกข้อมูล ---

# 1. หน้าต่างตั้งค่าเบอร์รับเงิน
class PaymentModal(Modal):
    def __init__(self):
        super().__init__(title="ตั้งค่าเบอร์รับเงิน")
        self.add_item(InputText(label="เบอร์วอลเล็ท / เลขบัญชี", placeholder="081xxxxxxx"))

    async def callback(self, interaction: discord.Interaction):
        shop_data["payment_number"] = self.children[0].value
        await interaction.response.send_message(f"✅ บันทึกเบอร์รับเงินเรียบร้อย: {shop_data['payment_number']}", ephemeral=True)

# 2. หน้าต่างเพิ่มสินค้า
class AddProductModal(Modal):
    def __init__(self):
        super().__init__(title="เพิ่มสินค้าใหม่")
        self.add_item(InputText(label="ชื่อสินค้า (เช่น YouTube, Netflix)", placeholder="Netflix 4K"))
        self.add_item(InputText(label="ราคา (บาท)", placeholder="120"))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value
        price = self.children[1].value
        
        if name in shop_data["products"]:
            await interaction.response.send_message("❌ มีสินค้านี้อยู่แล้ว", ephemeral=True)
        else:
            shop_data["products"][name] = {"price": int(price), "stock": []}
            await interaction.response.send_message(f"✅ เพิ่มสินค้า **{name}** ราคา **{price}** บาท เรียบร้อย", ephemeral=True)

# 3. หน้าต่างเติมสต็อก
class AddStockModal(Modal):
    def __init__(self):
        super().__init__(title="เติมสต็อกสินค้า")
        self.add_item(InputText(label="ชื่อสินค้าที่ต้องการเติม", placeholder="Netflix 4K"))
        self.add_item(InputText(label="ข้อมูลสินค้า (Email:Pass หรือ Code)", style=discord.InputTextStyle.paragraph))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value
        content = self.children[1].value.splitlines() # รองรับการเติมหลายบรรทัด
        
        if name in shop_data["products"]:
            shop_data["products"][name]["stock"].extend(content)
            count = len(content)
            await interaction.response.send_message(f"✅ เติมสต็อก **{name}** จำนวน {count} ชิ้น เรียบร้อย", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ ไม่พบสินค้าชื่อ **{name}** กรุณาเพิ่มสินค้าก่อน", ephemeral=True)

# 4. หน้าต่างลบสินค้า
class DeleteProductModal(Modal):
    def __init__(self):
        super().__init__(title="ลบสินค้า")
        self.add_item(InputText(label="ชื่อสินค้าที่ต้องการลบ", placeholder="Netflix 4K"))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value
        if name in shop_data["products"]:
            del shop_data["products"][name]
            await interaction.response.send_message(f"🗑️ ลบสินค้า **{name}** เรียบร้อยแล้ว", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ ไม่พบสินค้าชื่อ **{name}**", ephemeral=True)

# --- View: ตัวจัดการปุ่ม ---
class AdminPanel(View):
    def __init__(self):
        super().__init__(timeout=None) # ปุ่มไม่มีวันหมดอายุ

    @discord.ui.button(label="ตั้งค่าเบอร์รับเงิน", style=
# รันบอท
server_on()


    bot.run(os.getenv('TOKEN'))



