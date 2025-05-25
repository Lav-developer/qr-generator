import streamlit as st
import qrcode
from PIL import Image
import io
import re
from datetime import datetime
import qrcode.image.svg
from io import BytesIO
import pyperclip

# Constants
ERROR_CORRECT_LEVELS = {
    "Low": qrcode.constants.ERROR_CORRECT_L,
    "Medium": qrcode.constants.ERROR_CORRECT_M,
    "High": qrcode.constants.ERROR_CORRECT_Q,
    "Highest": qrcode.constants.ERROR_CORRECT_H
}

# Function to validate inputs
def validate_inputs(category, inputs):
    if category == "WiFi Password":
        if not inputs.get("wifi_ssid"):
            return "WiFi SSID is required!"
        if not inputs.get("wifi_password"):
            return "WiFi Password is required!"
    elif category == "Link":
        url = inputs.get("link", "")
        if not url:
            return "URL is required!"
        if not re.match(r'^https?://', url):
            return "URL should start with http:// or https://"
    elif category == "WhatsApp":
        phone = inputs.get("whatsapp_number", "")
        if not phone:
            return "Phone number is required!"
        if not re.match(r'^\+?[\d\s-]+$', phone):
            return "Invalid phone number format"
    elif category == "Email":
        email = inputs.get("email", "")
        if not email:
            return "Email address is required!"
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return "Invalid email format"
    elif category == "Event":
        if not inputs.get("event_title"):
            return "Event title is required!"
        try:
            datetime.strptime(inputs.get("event_start", ""), "%Y-%m-%dT%H:%M")
        except ValueError:
            return "Invalid start date/time format (use YYYY-MM-DDTHH:MM)"
    return None

# Function to format data based on category
def format_qr_data(category, inputs):
    if category == "Number":
        value = inputs.get("number", "").strip()
        if value:
            return f"number:{value}"
        return ""
    elif category == "WiFi Password":
        ssid = inputs.get("wifi_ssid", "").strip()
        password = inputs.get("wifi_password", "").strip()
        encryption = inputs.get("wifi_encryption", "WPA")
        if ssid and password:
            return f"WIFI:S:{ssid};T:{encryption};P:{password};;"
        return ""
    elif category == "Link":
        url = inputs.get("link", "").strip()
        if url:
            return url
        return ""
    elif category == "WhatsApp":
        phone = inputs.get("whatsapp_number", "").replace(" ", "").replace("-", "")
        if phone:
            return f"https://wa.me/{phone}"
        return ""
    elif category == "Text":
        value = inputs.get("text", "").strip()
        if value:
            return f"text:{value}"
        return ""
    elif category == "Email":
        email = inputs.get("email", "").strip()
        subject = inputs.get("email_subject", "").strip()
        body = inputs.get("email_body", "").strip()
        if email:
            formatted = f"mailto:{email}?subject={subject}&body={body}" if subject or body else f"mailto:{email}"
            return formatted
        return ""
    elif category == "Phone":
        phone = inputs.get("phone_number", "").replace(" ", "").replace("-", "")
        if phone:
            return f"tel:{phone}"
        return ""
    elif category == "SMS":
        phone = inputs.get("sms_number", "").replace(" ", "").replace("-", "")
        message = inputs.get("sms_message", "").strip()
        if phone:
            formatted = f"sms:{phone}?body={message}" if message else f"sms:{phone}"
            return formatted
        return ""
    elif category == "Location":
        location = inputs.get("manual_location", "").strip()
        if location:
            return f"location:{location}"
        return ""
    elif category == "Event":
        title = inputs.get("event_title", "").strip()
        start = inputs.get("event_start", "").strip()
        end = inputs.get("event_end", "").strip() or start
        location = inputs.get("event_location", "").strip()
        description = inputs.get("event_description", "").strip()
        if title and start:
            try:
                start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
                end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")
                ical = (
                    f"BEGIN:VCALENDAR\n"
                    f"VERSION:2.0\n"
                    f"BEGIN:VEVENT\n"
                    f"SUMMARY:{title}\n"
                    f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}\n"
                    f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}\n"
                    f"LOCATION:{location}\n"
                    f"DESCRIPTION:{description}\n"
                    f"END:VEVENT\n"
                    f"END:VCALENDAR"
                )
                return ical
            except ValueError:
                return ""
        return ""
    elif category == "Social Media":
        platform = inputs.get("social_platform", "twitter")
        username = inputs.get("social_username", "").strip()
        if username:
            base_urls = {
                "twitter": "https://twitter.com/",
                "instagram": "https://instagram.com/",
                "facebook": "https://facebook.com/",
                "linkedin": "https://linkedin.com/in/",
                "youtube": "https://youtube.com/@",
                "tiktok": "https://tiktok.com/@",
                "snapchat": "https://snapchat.com/add/",
                "pinterest": "https://pinterest.com/"
            }
            return f"{base_urls.get(platform, 'https://')}{username}"
        return ""
    elif category == "vCard":
        name = inputs.get("vcard_name", "").strip()
        phone = inputs.get("vcard_phone", "").strip()
        email = inputs.get("vcard_email", "").strip()
        if name:
            vcard = [
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN:{name}",
            ]
            if phone:
                vcard.append(f"TEL:{phone}")
            if email:
                vcard.append(f"EMAIL:{email}")
            vcard.append("END:VCARD")
            return "\n".join(vcard)
        return ""
    elif category == "Cryptocurrency":
        crypto_type = inputs.get("crypto_type", "bitcoin")
        address = inputs.get("crypto_address", "").strip()
        if address:
            return f"{crypto_type}:{address}"
        return ""
    elif category == "2D Barcode":
        value = inputs.get("barcode_text", "").strip()
        if value:
            return value
        return ""
    return ""

# Function to generate QR code with customization
@st.cache_data(show_spinner="Generating QR code...")
def generate_qr(data, qr_config):
    qr = qrcode.QRCode(
        version=qr_config["version"],
        box_size=qr_config["box_size"],
        border=qr_config["border"],
        error_correction=qr_config["error_correction"]
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(
        fill_color=qr_config["fill_color"],
        back_color=qr_config["back_color"]
    )
    
    # PNG
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG")
    png_bytes = png_buffer.getvalue()
    
    # SVG
    factory = qrcode.image.svg.SvgPathImage
    svg_img = qrcode.make(data, image_factory=factory)
    svg_buffer = BytesIO()
    svg_img.save(svg_buffer)
    svg_bytes = svg_buffer.getvalue()
    
    return png_bytes, svg_bytes

# Initialize session state
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
    st.session_state.qr_history = []

# App layout
st.set_page_config(
    page_title="QR Code Generator",
    page_icon="🔳",
    layout="wide"
)

# Sidebar for settings
with st.sidebar:
    st.header("QR Code Settings")
    qr_config = {
        "version": st.slider("QR Version", 1, 40, 1),
        "box_size": st.slider("Box Size", 5, 20, 10),
        "border": st.slider("Border Size", 1, 10, 4),
        "error_correction": ERROR_CORRECT_LEVELS[st.selectbox(
            "Error Correction",
            list(ERROR_CORRECT_LEVELS.keys()),
            index=1
        )],
        "fill_color": st.color_picker("QR Color", "#000000"),
        "back_color": st.color_picker("Background Color", "#FFFFFF")
    }
    
    st.divider()
    st.header("History")
    if st.session_state.qr_history:
        for i, item in enumerate(st.session_state.qr_history[-5:]):
            with st.expander(f"QR {i+1}: {item['category']}"):
                st.image(item["png"], width=100)
                if st.button(f"Reuse #{i+1}", key=f"reuse_{i}"):
                    st.session_state.inputs = item["inputs"]
                    st.rerun()
    else:
        st.info("No history yet")

# Main content
st.title("QR Code Generator Pro")
st.markdown("""
Create customized QR codes for various purposes. 
Select a category below and fill in the required information.
""")

with st.expander("📚 How to use", expanded=False):
    st.markdown("""
    1. **Select a category** from the dropdown
    2. **Fill in the required fields**
    3. **Customize** the QR code appearance in the sidebar
    4. **Generate** and download your QR code
    5. **Share** your QR code via email or social media
    """)

# Category selection
categories = [
    "Number", "WiFi Password", "Link", "WhatsApp", "Text",
    "Email", "Phone", "SMS", "Location", "Event",
    "Social Media", "vCard", "Cryptocurrency", "2D Barcode"
]

category = st.selectbox(
    "Select QR Code Category",
    categories,
    index=4  # Default to Text
)

# Reset unrelated inputs when category changes
if "current_category" not in st.session_state:
    st.session_state.current_category = category

if st.session_state.current_category != category:
    st.session_state.inputs = {}
    st.session_state.current_category = category

# Dynamic input fields
with st.form("qr_form"):
    cols = st.columns(2)
    
    if category == "Number":
        st.session_state.inputs["number"] = cols[0].text_input(
            "Enter Number",
            value=st.session_state.inputs.get("number", ""),
            placeholder="e.g., 1234567890",
            help="Enter any numerical value"
        )
    
    elif category == "WiFi Password":
        st.session_state.inputs["wifi_ssid"] = cols[0].text_input(
            "WiFi SSID",
            value=st.session_state.inputs.get("wifi_ssid", ""),
            placeholder="Your WiFi network name"
        )
        st.session_state.inputs["wifi_password"] = cols[1].text_input(
            "WiFi Password",
            value=st.session_state.inputs.get("wifi_password", ""),
            placeholder="Your WiFi password"
        )
        st.session_state.inputs["wifi_encryption"] = st.selectbox(
            "Encryption Type",
            ["WPA", "WPA2", "WEP", "None"],
            index=1
        )
    
    elif category == "Link":
        st.session_state.inputs["link"] = st.text_input(
            "Enter URL",
            value=st.session_state.inputs.get("link", ""),
            placeholder="https://example.com",
            help="Must start with http:// or https://"
        )
    
    elif category == "WhatsApp":
        st.session_state.inputs["whatsapp_number"] = st.text_input(
            "WhatsApp Number",
            value=st.session_state.inputs.get("whatsapp_number", ""),
            placeholder="+1234567890",
            help="Include country code"
        )
    
    elif category == "Text":
        st.session_state.inputs["text"] = st.text_area(
            "Enter Text",
            value=st.session_state.inputs.get("text", ""),
            placeholder="Any text you want to encode",
            height=100
        )
    
    elif category == "Email":
        st.session_state.inputs["email"] = cols[0].text_input(
            "Email Address",
            value=st.session_state.inputs.get("email", ""),
            placeholder="user@example.com"
        )
        st.session_state.inputs["email_subject"] = cols[1].text_input(
            "Subject (optional)",
            value=st.session_state.inputs.get("email_subject", "")
        )
        st.session_state.inputs["email_body"] = st.text_area(
            "Body (optional)",
            value=st.session_state.inputs.get("email_body", ""),
            height=100
        )
    
    elif category == "Phone":
        st.session_state.inputs["phone_number"] = st.text_input(
            "Phone Number",
            value=st.session_state.inputs.get("phone_number", ""),
            placeholder="+1234567890",
            help="Include country code"
        )
    
    elif category == "SMS":
        st.session_state.inputs["sms_number"] = cols[0].text_input(
            "Phone Number",
            value=st.session_state.inputs.get("sms_number", ""),
            placeholder="+1234567890"
        )
        st.session_state.inputs["sms_message"] = cols[1].text_area(
            "Message (optional)",
            value=st.session_state.inputs.get("sms_message", ""),
            height=100
        )
    
    elif category == "Location":
        st.session_state.inputs["manual_location"] = st.text_input(
            "Location",
            value=st.session_state.inputs.get("manual_location", ""),
            placeholder="e.g., New York, NY or 123 Main St"
        )
    
    elif category == "Event":
        st.session_state.inputs["event_title"] = cols[0].text_input(
            "Event Title",
            value=st.session_state.inputs.get("event_title", "")
        )
        st.session_state.inputs["event_start"] = cols[1].text_input(
            "Start Time",
            value=st.session_state.inputs.get("event_start", ""),
            placeholder="YYYY-MM-DDTHH:MM",
            help="Format: 2025-01-01T14:00"
        )
        st.session_state.inputs["event_end"] = cols[0].text_input(
            "End Time (optional)",
            value=st.session_state.inputs.get("event_end", ""),
            placeholder="YYYY-MM-DDTHH:MM"
        )
        st.session_state.inputs["event_location"] = cols[1].text_input(
            "Location (optional)",
            value=st.session_state.inputs.get("event_location", "")
        )
        st.session_state.inputs["event_description"] = st.text_area(
            "Description (optional)",
            value=st.session_state.inputs.get("event_description", ""),
            height=100
        )
    
    elif category == "Social Media":
        platform = st.selectbox(
            "Social Media Platform",
            ["twitter", "instagram", "facebook", "linkedin", "youtube", "tiktok", "snapchat", "pinterest"],
            index=0
        )
        st.session_state.inputs["social_platform"] = platform
        st.session_state.inputs["social_username"] = st.text_input(
            f"{platform.capitalize()} Username",
            value=st.session_state.inputs.get("social_username", ""),
            placeholder="username"
        )
    
    elif category == "vCard":
        st.session_state.inputs["vcard_name"] = cols[0].text_input(
            "Full Name",
            value=st.session_state.inputs.get("vcard_name", "")
        )
        st.session_state.inputs["vcard_phone"] = cols[1].text_input(
            "Phone (optional)",
            value=st.session_state.inputs.get("vcard_phone", "")
        )
        st.session_state.inputs["vcard_email"] = st.text_input(
            "Email (optional)",
            value=st.session_state.inputs.get("vcard_email", "")
        )
    
    elif category == "Cryptocurrency":
        crypto_type = st.selectbox(
            "Currency",
            ["bitcoin", "ethereum", "litecoin", "dogecoin"],
            index=0
        )
        st.session_state.inputs["crypto_type"] = crypto_type
        st.session_state.inputs["crypto_address"] = st.text_input(
            f"{crypto_type.capitalize()} Address",
            value=st.session_state.inputs.get("crypto_address", "")
        )
    
    elif category == "2D Barcode":
        st.session_state.inputs["barcode_text"] = st.text_area(
            "Enter Text",
            value=st.session_state.inputs.get("barcode_text", ""),
            height=100
        )
    
    # Preview of what will be encoded
    data_preview = format_qr_data(category, st.session_state.inputs)
    if data_preview:
        with st.expander("Preview encoded data"):
            st.code(data_preview, language="text")
    
    generate_btn = st.form_submit_button("Generate QR Code")

# Generate and display QR code
if generate_btn:
    error = validate_inputs(category, st.session_state.inputs)
    if error:
        st.error(error)
    else:
        data = format_qr_data(category, st.session_state.inputs)
        if data:
            with st.spinner("Generating QR code..."):
                png_bytes, svg_bytes = generate_qr(data, qr_config)
                
                # Save to history
                if len(st.session_state.qr_history) >= 10:
                    st.session_state.qr_history.pop(0)
                st.session_state.qr_history.append({
                    "category": category,
                    "inputs": st.session_state.inputs.copy(),
                    "png": png_bytes,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Display results
                col1, col2 = st.columns(2)
                with col1:
                    st.image(png_bytes, caption="Generated QR Code", use_container_width=True)
                    
                    # Copy to Clipboard Button
                    if st.button("📋 Copy QR to Clipboard", help="Copy the QR code image to your clipboard"):
                        try:
                            img = Image.open(io.BytesIO(png_bytes))
                            pyperclip.copy(img)
                            st.success("✅ Copied to clipboard!")
                        except Exception as e:
                            st.error(f"Failed to copy: {e}")
                
                with col2:
                    st.success("QR code generated successfully!")
                    
                    # Download Buttons
                    st.download_button(
                        label="Download PNG",
                        data=png_bytes,
                        file_name=f"qr_code_{category.lower().replace(' ', '_')}.png",
                        mime="image/png"
                    )
                    st.download_button(
                        label="Download SVG",
                        data=svg_bytes,
                        file_name=f"qr_code_{category.lower().replace(' ', '_')}.svg",
                        mime="image/svg+xml"
                    )
                    
                    st.markdown("**Encoded data:**")
                    st.code(data, language="text")
                    
                    # Share Options
                    st.markdown("### Share QR Code")
                    share_text = f"Check out this QR Code I generated! It links to: {data}"
                    
                    # Email Share
                    st.markdown(f"""
                    <a href="mailto:?subject=QR Code&body={share_text}" target="_blank">
                        <button style="background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                            📧 Share via Email
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Twitter Share
                    st.markdown(f"""
                    <a href="https://twitter.com/intent/tweet?text={share_text}" target="_blank">
                        <button style="background-color: #1DA1F2; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                            🐦 Share on Twitter
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # WhatsApp Share
                    st.markdown(f"""
                    <a href="https://wa.me/?text={share_text}" target="_blank">
                        <button style="background-color: #25D366; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                            💬 Share on WhatsApp
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
        else:
            st.error("Failed to generate QR code. Please check your inputs.")

# Footer
st.divider()
st.markdown("""
### Tips for Best Results
- For **links**, always include `https://`
- For **phone numbers**, include country code (e.g., +1 for US)
- For **WiFi**, double-check your password and encryption type
- Use the **Share** buttons to quickly send your QR code to others
""")

# Developer Footer
st.markdown("""
<style>
.footer {
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: auto;
    color: auto;
    text-align: center;
    padding: 10px;
    margin-top: 20px;
    border-top: 1px solid #e1e1e1;
}
</style>
<div class="footer">
    <p>Developed by Lav Kush | <a href="https://lav-developer.netlify.app" target="_blank">Portfolio</a></p>
</div>
""", unsafe_allow_html=True)
