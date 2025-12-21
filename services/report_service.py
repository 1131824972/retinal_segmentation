import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import io
import base64
from PIL import Image as PILImage


class ReportService:
    def generate_pdf(self, patient_data, prediction_data, report_data, image_base64):
        """
        生成PDF文件的二进制流
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # --- 1. 注册字体 (为了支持中文) ---
        # 这一步比较关键，Docker里可能没有中文字体，
        # 建议在项目里放一个 simhei.ttf (黑体) 文件，或者暂时用英文演示
        # c.setFont("Helvetica-Bold", 24)

        # --- 2. 绘制标题 ---
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 50, "Retinal Diagnosis Report")

        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 70, "Yunnan University - AI Medical Lab")
        c.line(50, height - 80, width - 50, height - 80)

        # --- 3. 病人信息 ---
        y_pos = height - 120
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "Patient Info")

        c.setFont("Helvetica", 12)
        c.drawString(50, y_pos - 25, f"Name: {patient_data.get('username', 'Unknown')}")
        c.drawString(300, y_pos - 25, f"Email: {patient_data.get('email', 'N/A')}")
        c.drawString(50, y_pos - 45, f"Report ID: {str(report_data.get('_id'))}")
        c.drawString(300, y_pos - 45, f"Date: {report_data['created_at'].strftime('%Y-%m-%d')}")

        # --- 4. 图像区域 (左边原图，右边血管图) ---
        # 这里需要把 base64 转成图片对象绘制
        try:
            # 假设传入的是处理后的血管图
            img_data = base64.b64decode(image_base64)
            img = ImageReader(io.BytesIO(img_data))
            # 画图 (x, y, width, height)
            c.drawImage(img, 150, height - 450, width=300, height=300, mask='auto')
            c.drawCentredString(width / 2, height - 460, "Vessel Segmentation Result")
        except Exception as e:
            c.drawString(50, height - 300, f"[Image Error: {str(e)}]")

        # --- 5. AI 分析指标 ---
        y_pos = height - 500
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "AI Analysis")

        c.setFont("Helvetica", 12)
        c.drawString(50, y_pos - 25,
                     f"Vessel Coverage: {prediction_data.get('result_data', {}).get('vessel_coverage', 0):.2%}")
        c.drawString(50, y_pos - 45,
                     f"Model Confidence: {prediction_data.get('result_data', {}).get('confidence', 0):.4f}")

        # --- 6. 医生诊断 ---
        y_pos = height - 580
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_pos, "Doctor's Diagnosis")

        c.setFont("Helvetica", 12)
        text_object = c.beginText(50, y_pos - 25)
        text_object.setFont("Helvetica", 12)
        # 简单换行处理
        notes = report_data.get('diagnosis_text', '')
        # 这里应该做自动换行逻辑，为了演示先截断
        text_object.textLines(notes[:200])
        c.drawText(text_object)

        # --- 7. 结论 ---
        y_pos = height - 700
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, f"Conclusion: {report_data.get('conclusion', 'Pending')}")
        c.drawString(350, y_pos, f"Doctor Signature: {report_data.get('doctor_name', '')}")

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer


report_service = ReportService()