from PIL import Image, ImageDraw, ImageFont
import io

class PNGService:
    def __init__(self):
        self.width = 1200
        self.height = 600
    
    def render_contract(self, contract_data: dict) -> io.BytesIO:
        """Generate contract receipt PNG"""
        img = Image.new('RGB', (self.width, self.height), color='#0f0f0f')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        draw.text((40, 80), "🗡️ SNIPERS CONTRACT", fill='#ffffff', font=title_font)
        draw.text((40, 160), f"Series: {contract_data['series']} — Ch.{contract_data['chapter']}", 
                  fill='#ffffff', font=body_font)
        draw.text((40, 220), f"Role: {contract_data['role'].upper()}", fill='#ffffff', font=body_font)
        draw.text((40, 280), f"Reward: +{contract_data['reward']} coins", fill='#ffffff', font=body_font)
        draw.text((40, 340), f"Operative: {contract_data['user_tag']}", fill='#ffffff', font=body_font)
        draw.text((40, 540), f"Contract #{contract_data['id']} — High Order", fill='#888888', font=body_font)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

png_service = PNGService()
