"""
Default document and notification templates seeded for every school.

Document templates: 12 types × 3 styles = 36 templates
Notification templates: 8 event triggers × 3 styles = 24 templates

Each document template dict:
  template_name, template_type, canvas_width_mm, canvas_height_mm,
  template_html, layout_json, is_default (True for first of each type)

Each notification template dict:
  name, event_trigger, channel, subject, body_template, is_active, is_default
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCHOOL_STYLE = """
<style>
  @page { margin: 0; }
  * { box-sizing: border-box; font-family: Arial, sans-serif; }
  body { margin: 0; padding: 0; }
</style>
"""


def _doctype(content: str) -> str:
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{_SCHOOL_STYLE}</head><body>{content}</body></html>"


# ---------------------------------------------------------------------------
# Document Templates
# ---------------------------------------------------------------------------

_STUDENT_ID_FRONT_CLASSIC = _doctype("""
<div style="width:85.6mm;height:54mm;background:#1a3a6b;color:#fff;position:relative;overflow:hidden;border-radius:4mm;">
  <div style="background:#e8b400;height:12mm;display:flex;align-items:center;padding:0 4mm;">
    <span style="font-size:11pt;font-weight:bold;letter-spacing:1px;">{{ school_name }}</span>
  </div>
  <div style="display:flex;padding:3mm;gap:3mm;">
    <img src="{{ photo_url }}" style="width:18mm;height:22mm;object-fit:cover;border:1mm solid #e8b400;border-radius:1mm;" onerror="this.style.display='none'"/>
    <div style="flex:1;">
      <div style="font-size:9pt;font-weight:bold;margin-bottom:1mm;">{{ student_name }}</div>
      <div style="font-size:7pt;margin-bottom:1mm;">Class: {{ class_name }} {{ section_name }}</div>
      <div style="font-size:7pt;margin-bottom:1mm;">Roll No: {{ roll_number }}</div>
      <div style="font-size:7pt;margin-bottom:1mm;">Adm No: {{ admission_number }}</div>
      <div style="font-size:7pt;">Session: {{ academic_year }}</div>
    </div>
    <img src="{{ qr_code_url }}" style="width:14mm;height:14mm;align-self:flex-end;" onerror="this.style.display='none'"/>
  </div>
  <div style="position:absolute;bottom:2mm;left:0;right:0;text-align:center;font-size:6pt;color:#aac0e8;">
    {{ school_address }}
  </div>
</div>
""")

_STUDENT_ID_FRONT_MODERN = _doctype("""
<div style="width:85.6mm;height:54mm;background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff;position:relative;border-radius:4mm;overflow:hidden;">
  <div style="position:absolute;top:-10mm;right:-10mm;width:35mm;height:35mm;background:rgba(255,255,255,0.08);border-radius:50%;"></div>
  <div style="padding:3mm 4mm;">
    <div style="font-size:10pt;font-weight:bold;color:#64d8f0;letter-spacing:0.5px;">{{ school_name }}</div>
    <div style="font-size:6pt;color:#aad4e0;margin-bottom:3mm;">STUDENT IDENTITY CARD</div>
    <div style="display:flex;gap:3mm;align-items:flex-start;">
      <img src="{{ photo_url }}" style="width:17mm;height:20mm;object-fit:cover;border-radius:2mm;border:0.5mm solid #64d8f0;" onerror="this.style.display='none'"/>
      <div>
        <div style="font-size:9pt;font-weight:bold;margin-bottom:1.5mm;">{{ student_name }}</div>
        <div style="font-size:7pt;line-height:1.6;">
          Class: {{ class_name }}-{{ section_name }}<br/>
          Roll: {{ roll_number }} | Adm: {{ admission_number }}<br/>
          DOB: {{ date_of_birth }}<br/>
          {{ academic_year }}
        </div>
      </div>
    </div>
  </div>
  <div style="position:absolute;bottom:2mm;right:3mm;">
    <img src="{{ qr_code_url }}" style="width:12mm;height:12mm;" onerror="this.style.display='none'"/>
  </div>
</div>
""")

_STUDENT_ID_FRONT_MINIMAL = _doctype("""
<div style="width:85.6mm;height:54mm;background:#fff;border:0.5mm solid #ddd;border-radius:3mm;overflow:hidden;">
  <div style="background:#f5f5f5;padding:2mm 4mm;border-bottom:0.5mm solid #ddd;">
    <div style="font-size:9pt;font-weight:bold;color:#222;">{{ school_name }}</div>
    <div style="font-size:6pt;color:#666;text-transform:uppercase;letter-spacing:1px;">Student ID Card &bull; {{ academic_year }}</div>
  </div>
  <div style="display:flex;padding:3mm;gap:3mm;align-items:flex-start;">
    <img src="{{ photo_url }}" style="width:16mm;height:19mm;object-fit:cover;border:0.5mm solid #ccc;" onerror="this.style.display='none'"/>
    <div style="flex:1;font-size:7.5pt;color:#222;line-height:1.7;">
      <strong>{{ student_name }}</strong><br/>
      Class: {{ class_name }} – {{ section_name }}<br/>
      Roll No: {{ roll_number }}<br/>
      Adm No: {{ admission_number }}
    </div>
    <img src="{{ qr_code_url }}" style="width:13mm;height:13mm;" onerror="this.style.display='none'"/>
  </div>
</div>
""")

_STUDENT_ID_BACK_CLASSIC = _doctype("""
<div style="width:85.6mm;height:54mm;background:#1a3a6b;color:#fff;border-radius:4mm;overflow:hidden;padding:3mm;">
  <div style="font-size:7pt;font-weight:bold;color:#e8b400;margin-bottom:2mm;">EMERGENCY CONTACT</div>
  <div style="font-size:7pt;line-height:1.7;">
    Father: {{ father_name }} &bull; {{ father_phone }}<br/>
    Mother: {{ mother_name }} &bull; {{ mother_phone }}<br/>
    Address: {{ address }}, {{ city }} – {{ pincode }}
  </div>
  <div style="margin-top:2mm;font-size:7pt;color:#e8b400;font-weight:bold;">Blood Group: {{ blood_group }}</div>
  <div style="margin-top:3mm;border-top:0.3mm solid #aac0e8;padding-top:2mm;font-size:6pt;color:#aac0e8;">
    If found, please return to:<br/>{{ school_name }}, {{ school_address }}<br/>Ph: {{ school_phone }}
  </div>
</div>
""")

_STUDENT_ID_BACK_MODERN = _doctype("""
<div style="width:85.6mm;height:54mm;background:linear-gradient(135deg,#0f2027,#203a43,#2c5364);color:#fff;border-radius:4mm;overflow:hidden;padding:3mm;">
  <div style="font-size:6pt;color:#64d8f0;text-transform:uppercase;letter-spacing:1px;margin-bottom:2mm;">Emergency Information</div>
  <div style="font-size:7pt;line-height:1.6;">
    Guardian: {{ father_name }} | {{ father_phone }}<br/>
    Address: {{ address }}, {{ city }}<br/>
    Blood Grp: <strong>{{ blood_group }}</strong> | DOB: {{ date_of_birth }}
  </div>
  <div style="margin-top:3mm;font-size:6pt;color:#aad4e0;border-top:0.3mm solid #64d8f0;padding-top:2mm;">
    {{ school_name }} &bull; {{ school_phone }}<br/>{{ school_email }}
  </div>
</div>
""")

_STUDENT_ID_BACK_MINIMAL = _doctype("""
<div style="width:85.6mm;height:54mm;background:#fff;border:0.5mm solid #ddd;border-radius:3mm;overflow:hidden;padding:3mm;">
  <div style="font-size:7pt;font-weight:bold;color:#444;margin-bottom:2mm;text-transform:uppercase;">Emergency Contact</div>
  <div style="font-size:7pt;color:#333;line-height:1.7;">
    Parent: {{ father_name }} ({{ father_phone }})<br/>
    Address: {{ address }}, {{ city }} – {{ pincode }}<br/>
    Blood Group: {{ blood_group }}
  </div>
  <div style="margin-top:3mm;border-top:0.5mm solid #eee;padding-top:2mm;font-size:6pt;color:#888;">
    Return to: {{ school_name }} | {{ school_phone }}
  </div>
</div>
""")

_STAFF_ID_FRONT_CLASSIC = _doctype("""
<div style="width:85.6mm;height:54mm;background:#2d5016;color:#fff;border-radius:4mm;overflow:hidden;">
  <div style="background:#8bc34a;height:10mm;display:flex;align-items:center;padding:0 4mm;">
    <span style="font-size:10pt;font-weight:bold;color:#1a3006;">{{ school_name }}</span>
  </div>
  <div style="display:flex;padding:3mm;gap:3mm;">
    <img src="{{ photo_url }}" style="width:18mm;height:21mm;object-fit:cover;border:1mm solid #8bc34a;border-radius:1mm;" onerror="this.style.display='none'"/>
    <div style="flex:1;font-size:7.5pt;line-height:1.7;">
      <div style="font-size:9pt;font-weight:bold;color:#8bc34a;">{{ staff_name }}</div>
      <div>{{ designation }}</div>
      <div>Dept: {{ department }}</div>
      <div>ID: {{ employee_id }}</div>
      <div style="font-size:6pt;color:#ccc;">Valid: {{ valid_from }} – {{ valid_until }}</div>
    </div>
    <img src="{{ qr_code_url }}" style="width:13mm;height:13mm;align-self:flex-end;" onerror="this.style.display='none'"/>
  </div>
</div>
""")

_STAFF_ID_FRONT_MODERN = _doctype("""
<div style="width:85.6mm;height:54mm;background:linear-gradient(135deg,#1b2838,#2a475e);color:#fff;border-radius:4mm;overflow:hidden;">
  <div style="padding:3mm 4mm;">
    <div style="font-size:9pt;font-weight:bold;color:#66c0f4;">{{ school_name }}</div>
    <div style="font-size:6pt;color:#8ba1b4;margin-bottom:2mm;text-transform:uppercase;letter-spacing:1px;">Staff Identity Card</div>
    <div style="display:flex;gap:3mm;">
      <img src="{{ photo_url }}" style="width:17mm;height:20mm;object-fit:cover;border-radius:2mm;border:0.5mm solid #66c0f4;" onerror="this.style.display='none'"/>
      <div style="font-size:7.5pt;line-height:1.6;">
        <strong>{{ staff_name }}</strong><br/>
        {{ designation }}<br/>
        {{ department }}<br/>
        EMP ID: {{ employee_id }}<br/>
        <span style="font-size:6pt;color:#8ba1b4;">{{ valid_from }} – {{ valid_until }}</span>
      </div>
    </div>
  </div>
  <div style="position:absolute;bottom:2mm;right:3mm;">
    <img src="{{ qr_code_url }}" style="width:11mm;height:11mm;" onerror="this.style.display='none'"/>
  </div>
</div>
""")

_STAFF_ID_FRONT_MINIMAL = _doctype("""
<div style="width:85.6mm;height:54mm;background:#fff;border:0.5mm solid #ddd;border-radius:3mm;overflow:hidden;">
  <div style="background:#f9f9f9;padding:2mm 4mm;border-bottom:0.5mm solid #ddd;">
    <div style="font-size:9pt;font-weight:bold;color:#222;">{{ school_name }}</div>
    <div style="font-size:6pt;color:#888;text-transform:uppercase;">Staff Identity Card</div>
  </div>
  <div style="display:flex;padding:3mm;gap:3mm;">
    <img src="{{ photo_url }}" style="width:16mm;height:19mm;object-fit:cover;border:0.5mm solid #ccc;" onerror="this.style.display='none'"/>
    <div style="flex:1;font-size:7.5pt;color:#222;line-height:1.7;">
      <strong>{{ staff_name }}</strong><br/>
      {{ designation }} | {{ department }}<br/>
      EMP ID: {{ employee_id }}<br/>
      <span style="font-size:6pt;color:#888;">Valid: {{ valid_from }} – {{ valid_until }}</span>
    </div>
    <img src="{{ qr_code_url }}" style="width:12mm;height:12mm;" onerror="this.style.display='none'"/>
  </div>
</div>
""")

_STAFF_ID_BACK_CLASSIC = _doctype("""
<div style="width:85.6mm;height:54mm;background:#2d5016;color:#fff;border-radius:4mm;overflow:hidden;padding:3mm;">
  <div style="font-size:7pt;font-weight:bold;color:#8bc34a;margin-bottom:2mm;">EMPLOYEE DETAILS</div>
  <div style="font-size:7pt;line-height:1.7;">
    Joining Date: {{ joining_date }}<br/>
    Qualification: {{ qualification }}<br/>
    Emergency: {{ emergency_contact }}<br/>
    Blood Group: {{ blood_group }}
  </div>
  <div style="margin-top:3mm;border-top:0.3mm solid #8bc34a;padding-top:2mm;font-size:6pt;color:#cde8a0;">
    {{ school_name }} | {{ school_address }}<br/>Ph: {{ school_phone }}
  </div>
</div>
""")

_STAFF_ID_BACK_MODERN = _doctype("""
<div style="width:85.6mm;height:54mm;background:linear-gradient(135deg,#1b2838,#2a475e);color:#fff;border-radius:4mm;overflow:hidden;padding:3mm;">
  <div style="font-size:6pt;color:#66c0f4;text-transform:uppercase;letter-spacing:1px;margin-bottom:2mm;">Employee Information</div>
  <div style="font-size:7pt;line-height:1.6;">
    Joined: {{ joining_date }} | Blood: {{ blood_group }}<br/>
    Qualification: {{ qualification }}<br/>
    Emergency: {{ emergency_contact }}
  </div>
  <div style="margin-top:3mm;border-top:0.3mm solid #66c0f4;padding-top:2mm;font-size:6pt;color:#8ba1b4;">
    {{ school_name }} &bull; {{ school_phone }} &bull; {{ school_email }}
  </div>
</div>
""")

_STAFF_ID_BACK_MINIMAL = _doctype("""
<div style="width:85.6mm;height:54mm;background:#fff;border:0.5mm solid #ddd;border-radius:3mm;overflow:hidden;padding:3mm;">
  <div style="font-size:7pt;font-weight:bold;color:#444;margin-bottom:2mm;">Employee Details</div>
  <div style="font-size:7pt;color:#333;line-height:1.7;">
    Joined: {{ joining_date }}<br/>
    Blood Group: {{ blood_group }}<br/>
    Emergency: {{ emergency_contact }}
  </div>
  <div style="margin-top:3mm;border-top:0.5mm solid #eee;padding-top:2mm;font-size:6pt;color:#888;">
    {{ school_name }} | {{ school_phone }}
  </div>
</div>
""")

# --- Admit Card ---
_A4_STYLE = "width:210mm;min-height:148mm;background:#fff;padding:10mm;font-family:Arial,sans-serif;"

_ADMIT_CARD_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="text-align:center;border-bottom:0.5mm solid #333;padding-bottom:5mm;margin-bottom:5mm;">
    <div style="font-size:14pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:9pt;color:#555;">{{{{ school_address }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:3mm;text-transform:uppercase;letter-spacing:1px;">Admit Card – {{{{ exam_name }}}}</div>
    <div style="font-size:9pt;">Academic Year: {{{{ academic_year }}}}</div>
  </div>
  <div style="display:flex;gap:8mm;margin-bottom:5mm;">
    <img src="{{{{ photo_url }}}}" style="width:30mm;height:35mm;object-fit:cover;border:0.5mm solid #333;" onerror="this.style.display='none'"/>
    <table style="flex:1;font-size:9pt;border-collapse:collapse;">
      <tr><td style="padding:1.5mm 3mm;background:#f5f5f5;font-weight:bold;width:40mm;">Student Name</td><td style="padding:1.5mm 3mm;">{{{{ student_name }}}}</td></tr>
      <tr><td style="padding:1.5mm 3mm;background:#f5f5f5;font-weight:bold;">Admission No.</td><td style="padding:1.5mm 3mm;">{{{{ admission_number }}}}</td></tr>
      <tr><td style="padding:1.5mm 3mm;background:#f5f5f5;font-weight:bold;">Class / Section</td><td style="padding:1.5mm 3mm;">{{{{ class_name }}}} – {{{{ section_name }}}}</td></tr>
      <tr><td style="padding:1.5mm 3mm;background:#f5f5f5;font-weight:bold;">Roll Number</td><td style="padding:1.5mm 3mm;">{{{{ roll_number }}}}</td></tr>
      <tr><td style="padding:1.5mm 3mm;background:#f5f5f5;font-weight:bold;">Date of Birth</td><td style="padding:1.5mm 3mm;">{{{{ date_of_birth }}}}</td></tr>
    </table>
  </div>
  <div style="font-size:9pt;font-weight:bold;margin-bottom:2mm;">Exam Schedule</div>
  <table style="width:100%;border-collapse:collapse;font-size:8.5pt;">
    <thead><tr style="background:#1a3a6b;color:#fff;">
      <th style="padding:2mm;text-align:left;">Subject</th>
      <th style="padding:2mm;">Date</th>
      <th style="padding:2mm;">Day</th>
      <th style="padding:2mm;">Time</th>
      <th style="padding:2mm;">Room</th>
    </tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr style="border-bottom:0.3mm solid #ddd;">
      <td style="padding:2mm;">{{{{ s.subject_name }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.exam_date }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.day }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.start_time }}}} – {{{{ s.end_time }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.room_number }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
  </table>
  <div style="margin-top:10mm;display:flex;justify-content:space-between;font-size:8pt;">
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:40mm;margin:0 auto;"></div>
      <div>Student Signature</div>
    </div>
    <div style="text-align:center;">
      <img src="{{{{ qr_code_url }}}}" style="width:18mm;height:18mm;" onerror="this.style.display='none'"/>
    </div>
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:40mm;margin:0 auto;"></div>
      <div>Principal Signature</div>
    </div>
  </div>
</div>
""")

_ADMIT_CARD_MODERN = _doctype(f"""
<div style="{_A4_STYLE}border-top:2mm solid #2c5364;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5mm;">
    <div>
      <div style="font-size:13pt;font-weight:bold;color:#2c5364;">{{{{ school_name }}}}</div>
      <div style="font-size:8pt;color:#666;">{{{{ school_address }}}}</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11pt;font-weight:bold;color:#203a43;">ADMIT CARD</div>
      <div style="font-size:8.5pt;">{{{{ exam_name }}}} | {{{{ academic_year }}}}</div>
    </div>
  </div>
  <div style="background:#f0f4f8;border-radius:2mm;padding:4mm;display:flex;gap:6mm;margin-bottom:5mm;">
    <img src="{{{{ photo_url }}}}" style="width:28mm;height:33mm;object-fit:cover;border-radius:2mm;" onerror="this.style.display='none'"/>
    <div style="flex:1;font-size:8.5pt;line-height:2;">
      <strong style="font-size:10pt;">{{{{ student_name }}}}</strong><br/>
      Adm #{{{{ admission_number }}}} &nbsp;|&nbsp; Roll: {{{{ roll_number }}}}<br/>
      Class: {{{{ class_name }}}} – {{{{ section_name }}}}<br/>
      DOB: {{{{ date_of_birth }}}}
    </div>
    <img src="{{{{ qr_code_url }}}}" style="width:20mm;height:20mm;align-self:flex-end;" onerror="this.style.display='none'"/>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:8.5pt;">
    <thead><tr style="background:#2c5364;color:#fff;">
      <th style="padding:2mm;text-align:left;border-radius:1mm 0 0 0;">Subject</th>
      <th style="padding:2mm;">Date</th><th style="padding:2mm;">Time</th><th style="padding:2mm;border-radius:0 1mm 0 0;">Room</th>
    </tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr style="background:{{% if loop.index is odd %}}#f9f9f9{{% else %}}#fff{{% endif %}};border-bottom:0.3mm solid #ddd;">
      <td style="padding:2mm;">{{{{ s.subject_name }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.exam_date }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.start_time }}}} – {{{{ s.end_time }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.room_number }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
  </table>
  <div style="margin-top:8mm;display:flex;justify-content:flex-end;">
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:40mm;margin:0 auto;padding-top:1mm;font-size:8pt;">Principal / Controller of Examinations</div>
    </div>
  </div>
</div>
""")

_ADMIT_CARD_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}">
  <table style="width:100%;border-collapse:collapse;border:0.5mm solid #ddd;margin-bottom:5mm;">
    <tr>
      <td colspan="3" style="background:#f5f5f5;padding:3mm;text-align:center;border-bottom:0.5mm solid #ddd;">
        <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
        <div style="font-size:9pt;">Admit Card – {{{{ exam_name }}}} ({{{{ academic_year }}}})</div>
      </td>
    </tr>
    <tr>
      <td style="padding:3mm;vertical-align:top;border-right:0.5mm solid #ddd;">
        <img src="{{{{ photo_url }}}}" style="width:28mm;height:33mm;object-fit:cover;" onerror="this.style.display='none'"/>
      </td>
      <td style="padding:3mm;vertical-align:top;font-size:9pt;line-height:1.8;">
        <strong>{{{{ student_name }}}}</strong><br/>
        Adm No: {{{{ admission_number }}}}<br/>
        Class: {{{{ class_name }}}} – {{{{ section_name }}}}<br/>
        Roll: {{{{ roll_number }}}}<br/>
        DOB: {{{{ date_of_birth }}}}
      </td>
      <td style="padding:3mm;vertical-align:bottom;text-align:center;border-left:0.5mm solid #ddd;">
        <img src="{{{{ qr_code_url }}}}" style="width:20mm;height:20mm;" onerror="this.style.display='none'"/>
      </td>
    </tr>
  </table>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr style="background:#eee;"><th style="padding:2mm;text-align:left;border:0.3mm solid #ccc;">Subject</th><th style="padding:2mm;border:0.3mm solid #ccc;">Date</th><th style="padding:2mm;border:0.3mm solid #ccc;">Time</th><th style="padding:2mm;border:0.3mm solid #ccc;">Room</th></tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr><td style="padding:2mm;border:0.3mm solid #ccc;">{{{{ s.subject_name }}}}</td><td style="padding:2mm;border:0.3mm solid #ccc;text-align:center;">{{{{ s.exam_date }}}}</td><td style="padding:2mm;border:0.3mm solid #ccc;text-align:center;">{{{{ s.start_time }}}} – {{{{ s.end_time }}}}</td><td style="padding:2mm;border:0.3mm solid #ccc;text-align:center;">{{{{ s.room_number }}}}</td></tr>
    {{% endfor %}}
    </tbody>
  </table>
</div>
""")

# --- Fee Receipt ---
_FEE_RECEIPT_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #1a3a6b;">
  <div style="text-align:center;margin-bottom:5mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}} | {{{{ school_phone }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:3mm;border-top:0.3mm solid #1a3a6b;border-bottom:0.3mm solid #1a3a6b;padding:2mm;color:#1a3a6b;">FEE RECEIPT</div>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:9pt;margin-bottom:4mm;">
    <div>Receipt No: <strong>{{{{ receipt_number }}}}</strong></div>
    <div>Date: <strong>{{{{ payment_date }}}}</strong></div>
  </div>
  <div style="background:#f5f5f5;padding:3mm;border-radius:1mm;font-size:9pt;margin-bottom:4mm;">
    <div><strong>Student:</strong> {{{{ student_name }}}} &nbsp;|&nbsp; <strong>Class:</strong> {{{{ class_name }}}} – {{{{ section_name }}}}</div>
    <div><strong>Adm No:</strong> {{{{ admission_number }}}} &nbsp;|&nbsp; <strong>Academic Year:</strong> {{{{ academic_year }}}}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr style="background:#1a3a6b;color:#fff;">
      <th style="padding:2.5mm;text-align:left;">Fee Head</th>
      <th style="padding:2.5mm;text-align:right;">Amount (₹)</th>
    </tr></thead>
    <tbody>
    {{% for item in fee_items %}}
    <tr style="border-bottom:0.3mm solid #ddd;">
      <td style="padding:2.5mm;">{{{{ item.fee_head }}}}</td>
      <td style="padding:2.5mm;text-align:right;">{{{{ item.amount }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
    <tfoot>
      <tr style="background:#f0f0f0;font-weight:bold;">
        <td style="padding:2.5mm;border-top:0.5mm solid #1a3a6b;">Total Paid</td>
        <td style="padding:2.5mm;text-align:right;border-top:0.5mm solid #1a3a6b;">₹ {{{{ total_amount }}}}</td>
      </tr>
      <tr><td colspan="2" style="padding:2.5mm;font-size:8pt;">Payment Mode: {{{{ payment_mode }}}} &nbsp;|&nbsp; Transaction Ref: {{{{ transaction_ref }}}}</td></tr>
    </tfoot>
  </table>
  <div style="margin-top:12mm;display:flex;justify-content:space-between;font-size:8pt;">
    <div><em>This is a computer generated receipt.</em></div>
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:40mm;margin:0 auto;"></div>
      <div>Authorised Signatory</div>
    </div>
  </div>
</div>
""")

_FEE_RECEIPT_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#2c5364,#203a43);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:5mm;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
        <div style="font-size:7.5pt;color:#aad4e0;">{{{{ school_address }}}}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:10pt;font-weight:bold;color:#64d8f0;">FEE RECEIPT</div>
        <div style="font-size:8pt;">#{{{{ receipt_number }}}}</div>
      </div>
    </div>
  </div>
  <div style="display:flex;gap:6mm;margin-bottom:5mm;font-size:9pt;">
    <div style="flex:1;background:#f0f4f8;padding:3mm;border-radius:2mm;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Student Details</div>
      <strong>{{{{ student_name }}}}</strong><br/>
      {{{{ class_name }}}} – {{{{ section_name }}}} | Adm: {{{{ admission_number }}}}<br/>
      {{{{ academic_year }}}}
    </div>
    <div style="background:#f0f4f8;padding:3mm;border-radius:2mm;text-align:right;font-size:9pt;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Payment Info</div>
      Date: <strong>{{{{ payment_date }}}}</strong><br/>
      Mode: {{{{ payment_mode }}}}<br/>
      Ref: {{{{ transaction_ref }}}}
    </div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr style="border-bottom:0.5mm solid #2c5364;">
      <th style="padding:2mm;text-align:left;color:#2c5364;">Fee Head</th>
      <th style="padding:2mm;text-align:right;color:#2c5364;">Amount</th>
    </tr></thead>
    <tbody>
    {{% for item in fee_items %}}
    <tr style="border-bottom:0.2mm solid #eee;">
      <td style="padding:2.5mm;">{{{{ item.fee_head }}}}</td>
      <td style="padding:2.5mm;text-align:right;">₹ {{{{ item.amount }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
    <tfoot><tr style="background:#2c5364;color:#fff;font-size:10pt;font-weight:bold;">
      <td style="padding:3mm;">Total Paid</td>
      <td style="padding:3mm;text-align:right;">₹ {{{{ total_amount }}}}</td>
    </tr></tfoot>
  </table>
  <div style="margin-top:8mm;font-size:7.5pt;color:#999;text-align:center;">Computer generated receipt — no signature required.</div>
</div>
""")

_FEE_RECEIPT_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}border-top:1mm solid #333;">
  <div style="margin-bottom:5mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#666;">{{{{ school_address }}}}</div>
    <div style="font-size:10pt;font-weight:bold;margin-top:2mm;">Fee Receipt &nbsp; #{{{{ receipt_number }}}}</div>
    <div style="font-size:8.5pt;color:#555;">Date: {{{{ payment_date }}}}</div>
  </div>
  <div style="border:0.3mm solid #ddd;padding:3mm;margin-bottom:4mm;font-size:9pt;">
    Student: <strong>{{{{ student_name }}}}</strong> | Class: {{{{ class_name }}}} | Adm: {{{{ admission_number }}}} | Year: {{{{ academic_year }}}}
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr><th style="padding:2mm;text-align:left;border-bottom:0.5mm solid #333;">Fee Head</th><th style="padding:2mm;text-align:right;border-bottom:0.5mm solid #333;">Amount</th></tr></thead>
    <tbody>
    {{% for item in fee_items %}}
    <tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ item.fee_head }}}}</td><td style="padding:2mm;text-align:right;">₹ {{{{ item.amount }}}}</td></tr>
    {{% endfor %}}
    </tbody>
    <tfoot><tr style="font-weight:bold;border-top:0.5mm solid #333;"><td style="padding:2mm;">Total</td><td style="padding:2mm;text-align:right;">₹ {{{{ total_amount }}}}</td></tr></tfoot>
  </table>
  <div style="margin-top:4mm;font-size:8pt;color:#666;">Mode: {{{{ payment_mode }}}} | Ref: {{{{ transaction_ref }}}}</div>
</div>
""")

# --- Report Card ---
_REPORT_CARD_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="text-align:center;margin-bottom:6mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:2mm;color:#1a3a6b;">PROGRESS REPORT CARD</div>
    <div style="font-size:9pt;">{{{{ exam_name }}}} | Academic Year: {{{{ academic_year }}}}</div>
  </div>
  <div style="display:flex;gap:6mm;margin-bottom:5mm;font-size:9pt;">
    <div style="flex:1;">Student: <strong>{{{{ student_name }}}}</strong></div>
    <div>Class: <strong>{{{{ class_name }}}} – {{{{ section_name }}}}</strong></div>
    <div>Roll: <strong>{{{{ roll_number }}}}</strong></div>
    <div>Adm: <strong>{{{{ admission_number }}}}</strong></div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr style="background:#1a3a6b;color:#fff;">
      <th style="padding:2.5mm;text-align:left;">Subject</th>
      <th style="padding:2.5mm;text-align:center;">Max Marks</th>
      <th style="padding:2.5mm;text-align:center;">Marks Obtained</th>
      <th style="padding:2.5mm;text-align:center;">Grade</th>
      <th style="padding:2.5mm;text-align:center;">Remarks</th>
    </tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr style="border-bottom:0.3mm solid #ddd;background:{{% if loop.index is odd %}}#f9f9f9{{% else %}}#fff{{% endif %}};">
      <td style="padding:2.5mm;">{{{{ s.subject_name }}}}</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ s.max_marks }}}}</td>
      <td style="padding:2.5mm;text-align:center;font-weight:bold;">{{{{ s.marks_obtained }}}}</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ s.grade }}}}</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ s.remarks }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
    <tfoot><tr style="background:#e8f0fe;font-weight:bold;">
      <td style="padding:2.5mm;" colspan="2">Total / Percentage</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ total_marks_obtained }}}} / {{{{ total_max_marks }}}}</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ percentage }}}}%</td>
      <td style="padding:2.5mm;text-align:center;">{{{{ overall_grade }}}}</td>
    </tr></tfoot>
  </table>
  <div style="margin-top:4mm;font-size:9pt;">
    <strong>Result:</strong> {{{{ result_status }}}} &nbsp;|&nbsp; <strong>Rank:</strong> {{{{ rank }}}} &nbsp;|&nbsp; <strong>Attendance:</strong> {{{{ attendance_percentage }}}}%
  </div>
  <div style="margin-top:10mm;display:flex;justify-content:space-between;font-size:8pt;">
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Class Teacher</div></div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Principal</div></div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Parent / Guardian</div></div>
  </div>
</div>
""")

_REPORT_CARD_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#1a3a6b,#2c5364);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:6mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#aac0e8;">Progress Report Card &nbsp; | &nbsp; {{{{ exam_name }}}} &nbsp; | &nbsp; {{{{ academic_year }}}}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4mm;margin-bottom:5mm;font-size:9pt;">
    <div style="background:#f0f4f8;padding:3mm;border-radius:2mm;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Student</div>
      <strong>{{{{ student_name }}}}</strong><br/>
      {{{{ class_name }}}} – {{{{ section_name }}}} | Roll: {{{{ roll_number }}}}<br/>
      Adm: {{{{ admission_number }}}}
    </div>
    <div style="background:#f0f4f8;padding:3mm;border-radius:2mm;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Performance</div>
      Total: <strong>{{{{ total_marks_obtained }}}}/{{{{ total_max_marks }}}}</strong><br/>
      Percentage: <strong>{{{{ percentage }}}}%</strong> | Grade: <strong>{{{{ overall_grade }}}}</strong><br/>
      Rank: {{{{ rank }}}} | Attendance: {{{{ attendance_percentage }}}}%
    </div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:8.5pt;">
    <thead><tr style="background:#1a3a6b;color:#fff;">
      <th style="padding:2mm;text-align:left;">Subject</th>
      <th style="padding:2mm;text-align:center;">Max</th>
      <th style="padding:2mm;text-align:center;">Obtained</th>
      <th style="padding:2mm;text-align:center;">%</th>
      <th style="padding:2mm;text-align:center;">Grade</th>
    </tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr style="border-bottom:0.2mm solid #ddd;background:{{% if loop.index is odd %}}#f9f9f9{{% else %}}#fff{{% endif %}};">
      <td style="padding:2mm;">{{{{ s.subject_name }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.max_marks }}}}</td>
      <td style="padding:2mm;text-align:center;font-weight:bold;">{{{{ s.marks_obtained }}}}</td>
      <td style="padding:2mm;text-align:center;">{{{{ s.percentage }}}}%</td>
      <td style="padding:2mm;text-align:center;color:#1a3a6b;font-weight:bold;">{{{{ s.grade }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
  </table>
  <div style="margin-top:12mm;display:flex;justify-content:flex-end;gap:20mm;font-size:8pt;">
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:35mm;margin-bottom:1mm;"></div>Class Teacher</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:35mm;margin-bottom:1mm;"></div>Principal</div>
  </div>
</div>
""")

_REPORT_CARD_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}border-top:1mm solid #333;">
  <div style="margin-bottom:5mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#666;">Progress Report — {{{{ exam_name }}}} | {{{{ academic_year }}}}</div>
  </div>
  <div style="border:0.3mm solid #ddd;padding:3mm;margin-bottom:4mm;font-size:9pt;">
    <strong>{{{{ student_name }}}}</strong> | Class: {{{{ class_name }}}} – {{{{ section_name }}}} | Roll: {{{{ roll_number }}}} | Adm: {{{{ admission_number }}}}
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <thead><tr><th style="padding:2mm;text-align:left;border-bottom:0.5mm solid #333;">Subject</th><th style="padding:2mm;text-align:center;border-bottom:0.5mm solid #333;">Max</th><th style="padding:2mm;text-align:center;border-bottom:0.5mm solid #333;">Obtained</th><th style="padding:2mm;text-align:center;border-bottom:0.5mm solid #333;">Grade</th></tr></thead>
    <tbody>
    {{% for s in subjects %}}
    <tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ s.subject_name }}}}</td><td style="padding:2mm;text-align:center;">{{{{ s.max_marks }}}}</td><td style="padding:2mm;text-align:center;font-weight:bold;">{{{{ s.marks_obtained }}}}</td><td style="padding:2mm;text-align:center;">{{{{ s.grade }}}}</td></tr>
    {{% endfor %}}
    </tbody>
    <tfoot><tr style="font-weight:bold;border-top:0.5mm solid #333;"><td style="padding:2mm;" colspan="2">Percentage</td><td style="padding:2mm;text-align:center;">{{{{ percentage }}}}%</td><td style="padding:2mm;text-align:center;">{{{{ overall_grade }}}}</td></tr></tfoot>
  </table>
  <div style="margin-top:3mm;font-size:8.5pt;">Result: <strong>{{{{ result_status }}}}</strong> | Rank: {{{{ rank }}}} | Attendance: {{{{ attendance_percentage }}}}%</div>
</div>
""")

# --- Transfer Certificate ---
_TC_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="text-align:center;margin-bottom:6mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}} | {{{{ school_phone }}}}</div>
    <div style="font-size:12pt;font-weight:bold;margin-top:3mm;text-decoration:underline;color:#1a3a6b;">TRANSFER CERTIFICATE</div>
    <div style="font-size:8.5pt;">TC No: {{{{ tc_number }}}} &nbsp;|&nbsp; Date: {{{{ issue_date }}}}</div>
  </div>
  <div style="font-size:9.5pt;line-height:2.2;">
    <table style="width:100%;border-collapse:collapse;">
      {{% for row in [
        ('Student Name', student_name),
        ("Father's Name", father_name),
        ("Mother's Name", mother_name),
        ('Date of Birth', date_of_birth),
        ('Admission No.', admission_number),
        ('Date of Admission', admission_date),
        ('Class Last Studied', class_last_studied),
        ('Date of Leaving', date_of_leaving),
        ('Reason for Leaving', reason_for_leaving),
        ('Character & Conduct', character_and_conduct),
        ('Attendance', attendance_record),
        ('Eligible for Re-Admission', eligible_for_readmission),
      ] %}}
      <tr>
        <td style="padding:1.5mm 3mm;width:55mm;font-weight:bold;border-bottom:0.2mm solid #e0e0e0;">{{{{ row[0] }}}}</td>
        <td style="padding:1.5mm 3mm;border-bottom:0.2mm solid #e0e0e0;">: &nbsp;{{{{ row[1] }}}}</td>
      </tr>
      {{% endfor %}}
    </table>
  </div>
  <div style="margin-top:10mm;font-size:9pt;font-style:italic;">
    Certified that the above information is correct to the best of our knowledge.
  </div>
  <div style="margin-top:12mm;display:flex;justify-content:space-between;font-size:8.5pt;">
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Class Teacher</div></div>
    <div style="text-align:center;"><img src="{{{{ school_seal_url }}}}" style="width:20mm;height:20mm;" onerror="this.style.display='none'"/></div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Principal</div></div>
  </div>
</div>
""")

_TC_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#1a3a6b,#2c5364);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:6mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#aac0e8;">Transfer Certificate &nbsp;|&nbsp; TC No: {{{{ tc_number }}}} &nbsp;|&nbsp; Date: {{{{ issue_date }}}}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9.5pt;">
    <tbody>
    {{% set rows = [
      ('Student Name', student_name), ("Father's Name", father_name), ("Mother's Name", mother_name),
      ('Date of Birth', date_of_birth), ('Admission No.', admission_number), ('Date of Admission', admission_date),
      ('Class Last Studied', class_last_studied), ('Date of Leaving', date_of_leaving),
      ('Reason for Leaving', reason_for_leaving), ('Character & Conduct', character_and_conduct),
      ('Attendance', attendance_record), ('Eligible for Re-Admission', eligible_for_readmission),
    ] %}}
    {{% for label, value in rows %}}
    <tr style="background:{{% if loop.index is odd %}}#f0f4f8{{% else %}}#fff{{% endif %}};">
      <td style="padding:2mm 4mm;font-weight:bold;width:60mm;color:#1a3a6b;">{{{{ label }}}}</td>
      <td style="padding:2mm 4mm;">{{{{ value }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
  </table>
  <div style="margin-top:12mm;display:flex;justify-content:flex-end;gap:20mm;font-size:8pt;">
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;margin-bottom:1mm;"></div>Class Teacher</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;margin-bottom:1mm;"></div>Principal</div>
  </div>
</div>
""")

_TC_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}border-top:1mm solid #333;">
  <div style="margin-bottom:5mm;text-align:center;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:10pt;font-weight:bold;margin-top:2mm;">Transfer Certificate</div>
    <div style="font-size:8.5pt;color:#555;">TC No: {{{{ tc_number }}}} | Date: {{{{ issue_date }}}}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:9.5pt;">
    <tbody>
    {{% for label, value in [
      ('Student Name', student_name), ("Father's Name", father_name), ('Date of Birth', date_of_birth),
      ('Admission No.', admission_number), ('Class Last Studied', class_last_studied),
      ('Date of Leaving', date_of_leaving), ('Reason for Leaving', reason_for_leaving),
      ('Character & Conduct', character_and_conduct), ('Re-Admission Eligible', eligible_for_readmission),
    ] %}}
    <tr style="border-bottom:0.2mm solid #eee;">
      <td style="padding:1.5mm 0;font-weight:bold;width:55mm;">{{{{ label }}}}</td>
      <td style="padding:1.5mm 3mm;">{{{{ value }}}}</td>
    </tr>
    {{% endfor %}}
    </tbody>
  </table>
  <div style="margin-top:12mm;display:flex;justify-content:space-between;font-size:8pt;">
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:35mm;"></div>Class Teacher</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:35mm;"></div>Principal</div>
  </div>
</div>
""")

# --- Bonafide Certificate ---
_BONAFIDE_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="text-align:center;margin-bottom:8mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}} | Reg. No: {{{{ school_reg_number }}}}</div>
    <div style="font-size:12pt;font-weight:bold;margin-top:3mm;text-decoration:underline;color:#1a3a6b;">BONAFIDE CERTIFICATE</div>
  </div>
  <div style="font-size:10pt;line-height:2.0;text-align:justify;">
    <p>This is to certify that <strong>{{{{ student_name }}}}</strong>, son/daughter of
    <strong>{{{{ father_name }}}}</strong> and <strong>{{{{ mother_name }}}}</strong>,
    is a <em>bona fide</em> student of this institution, studying in
    <strong>Class {{{{ class_name }}}} – {{{{ section_name }}}}</strong> during the academic year
    <strong>{{{{ academic_year }}}}</strong>.</p>
    <p>His/Her admission number is <strong>{{{{ admission_number }}}}</strong> and
    date of birth as per school records is <strong>{{{{ date_of_birth }}}}</strong>.</p>
    <p>This certificate is issued for the purpose of <strong>{{{{ purpose }}}}</strong>.</p>
  </div>
  <div style="margin-top:12mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}</div>
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:45mm;"></div>
      <div>Principal</div>
      <div style="font-size:8pt;">{{{{ school_name }}}}</div>
    </div>
  </div>
</div>
""")

_BONAFIDE_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#1a3a6b,#2c5364);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:8mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#aac0e8;">{{{{ school_address }}}} | Reg No: {{{{ school_reg_number }}}}</div>
    <div style="font-size:10pt;font-weight:bold;color:#64d8f0;margin-top:2mm;">BONAFIDE CERTIFICATE</div>
  </div>
  <div style="font-size:10pt;line-height:2.0;text-align:justify;color:#222;">
    <p>This is to certify that <strong>{{{{ student_name }}}}</strong>, son/daughter of <strong>{{{{ father_name }}}}</strong>,
    is a <em>bona fide</em> student of this school, enrolled in <strong>Class {{{{ class_name }}}} – {{{{ section_name }}}}</strong>
    for the session <strong>{{{{ academic_year }}}}</strong>.</p>
    <p>Admission No: <strong>{{{{ admission_number }}}}</strong> &nbsp;|&nbsp; Date of Birth: <strong>{{{{ date_of_birth }}}}</strong></p>
    <p>Certificate issued for: <strong>{{{{ purpose }}}}</strong>.</p>
  </div>
  <div style="margin-top:12mm;text-align:right;font-size:9pt;">
    <div style="display:inline-block;text-align:center;">
      <div style="border-top:0.3mm solid #333;width:45mm;margin:0 auto;"></div>
      <div>Principal, {{{{ school_name }}}}</div>
      <div style="font-size:8pt;color:#666;">Date: {{{{ issue_date }}}}</div>
    </div>
  </div>
</div>
""")

_BONAFIDE_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="text-align:center;margin-bottom:8mm;border-bottom:0.5mm solid #333;padding-bottom:4mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#666;">{{{{ school_address }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:3mm;">Bonafide Certificate</div>
  </div>
  <div style="font-size:10.5pt;line-height:2.2;text-align:justify;">
    This is to certify that <strong>{{{{ student_name }}}}</strong>, Adm No: <strong>{{{{ admission_number }}}}</strong>,
    is studying in <strong>Class {{{{ class_name }}}} – {{{{ section_name }}}}</strong>, Academic Year <strong>{{{{ academic_year }}}}</strong>.
    Date of Birth: <strong>{{{{ date_of_birth }}}}</strong>.
    This certificate is issued for <strong>{{{{ purpose }}}}</strong>.
  </div>
  <div style="margin-top:14mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Principal</div></div>
  </div>
</div>
""")

# --- Character Certificate ---
_CHAR_CERT_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="text-align:center;margin-bottom:8mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}}</div>
    <div style="font-size:12pt;font-weight:bold;margin-top:3mm;text-decoration:underline;color:#1a3a6b;">CHARACTER CERTIFICATE</div>
  </div>
  <div style="font-size:10pt;line-height:2.2;text-align:justify;">
    <p>This is to certify that <strong>{{{{ student_name }}}}</strong>, son/daughter of <strong>{{{{ father_name }}}}</strong>,
    a student of <strong>Class {{{{ class_name }}}}</strong> (Session: <strong>{{{{ academic_year }}}}</strong>),
    Admission No. <strong>{{{{ admission_number }}}}</strong>, has been known to us since <strong>{{{{ admission_date }}}}</strong>.</p>
    <p>During his/her association with this institution, he/she has borne an excellent
    moral character and maintained <strong>{{{{ conduct }}}}</strong> conduct throughout.</p>
    <p>He/She has always been sincere in studies and participated actively in extracurricular activities.
    We wish him/her every success in future endeavours.</p>
  </div>
  <div style="margin-top:12mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}<br/>Place: {{{{ city }}}}</div>
    <div style="text-align:center;">
      <div style="border-top:0.3mm solid #333;width:45mm;"></div>
      <div>Principal</div><div style="font-size:8pt;">{{{{ school_name }}}}</div>
    </div>
  </div>
</div>
""")

_CHAR_CERT_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#1a3a6b,#2c5364);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:8mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#aac0e8;">{{{{ school_address }}}}</div>
    <div style="font-size:10pt;font-weight:bold;color:#64d8f0;margin-top:2mm;">CHARACTER CERTIFICATE</div>
  </div>
  <div style="font-size:10pt;line-height:2.2;text-align:justify;">
    This is to certify that <strong>{{{{ student_name }}}}</strong> (Adm: {{{{ admission_number }}}}),
    son/daughter of <strong>{{{{ father_name }}}}</strong>, studied in Class <strong>{{{{ class_name }}}}</strong>
    during session <strong>{{{{ academic_year }}}}</strong>.<br/>
    His/Her conduct and character has been <strong>{{{{ conduct }}}}</strong> throughout.
    He/She has been a diligent and well-behaved student.
    We wish him/her the very best for the future.
  </div>
  <div style="margin-top:12mm;text-align:right;font-size:9pt;">
    <div style="display:inline-block;text-align:center;">
      <div style="border-top:0.3mm solid #333;width:45mm;margin:0 auto;"></div>
      <div>Principal, {{{{ school_name }}}}</div>
      <div style="font-size:8pt;color:#666;">Date: {{{{ issue_date }}}}</div>
    </div>
  </div>
</div>
""")

_CHAR_CERT_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="text-align:center;margin-bottom:8mm;border-bottom:0.5mm solid #333;padding-bottom:4mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:3mm;">Character Certificate</div>
  </div>
  <div style="font-size:10.5pt;line-height:2.2;text-align:justify;">
    This is to certify that <strong>{{{{ student_name }}}}</strong> (Adm: <strong>{{{{ admission_number }}}}</strong>),
    Class <strong>{{{{ class_name }}}}</strong>, Session <strong>{{{{ academic_year }}}}</strong>,
    has maintained <strong>{{{{ conduct }}}}</strong> conduct. He/She has been a sincere and well-behaved student.
  </div>
  <div style="margin-top:14mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Principal</div></div>
  </div>
</div>
""")

# --- Payslip ---
_PAYSLIP_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="background:#1a3a6b;color:#fff;padding:4mm 6mm;margin-bottom:5mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:8pt;color:#aac0e8;">{{{{ school_address }}}}</div>
    <div style="font-size:10pt;font-weight:bold;margin-top:2mm;">SALARY SLIP — {{{{ pay_month }}}} {{{{ pay_year }}}}</div>
  </div>
  <div style="display:flex;gap:6mm;margin-bottom:5mm;font-size:9pt;">
    <div style="flex:1;background:#f5f5f5;padding:3mm;border-radius:1mm;">
      <strong>{{{{ staff_name }}}}</strong><br/>
      {{{{ designation }}}} | {{{{ department }}}}<br/>
      EMP ID: {{{{ employee_id }}}} | Bank A/C: {{{{ bank_account }}}}
    </div>
    <div style="background:#f5f5f5;padding:3mm;border-radius:1mm;font-size:9pt;">
      PAN: {{{{ pan_number }}}}<br/>
      PF No: {{{{ pf_number }}}}<br/>
      Days Worked: {{{{ days_worked }}}} / {{{{ total_days }}}}
    </div>
  </div>
  <div style="display:flex;gap:6mm;">
    <table style="flex:1;border-collapse:collapse;font-size:9pt;">
      <thead><tr style="background:#2c5364;color:#fff;"><th style="padding:2mm;text-align:left;" colspan="2">EARNINGS</th></tr></thead>
      <tbody>
      {{% for e in earnings %}}
      <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">{{{{ e.component }}}}</td><td style="padding:2mm;text-align:right;">₹ {{{{ e.amount }}}}</td></tr>
      {{% endfor %}}
      </tbody>
      <tfoot><tr style="background:#e8f0fe;font-weight:bold;"><td style="padding:2mm;">Gross Salary</td><td style="padding:2mm;text-align:right;">₹ {{{{ gross_salary }}}}</td></tr></tfoot>
    </table>
    <table style="flex:1;border-collapse:collapse;font-size:9pt;">
      <thead><tr style="background:#8b1a1a;color:#fff;"><th style="padding:2mm;text-align:left;" colspan="2">DEDUCTIONS</th></tr></thead>
      <tbody>
      {{% for d in deductions %}}
      <tr style="border-bottom:0.2mm solid #ddd;"><td style="padding:2mm;">{{{{ d.component }}}}</td><td style="padding:2mm;text-align:right;">₹ {{{{ d.amount }}}}</td></tr>
      {{% endfor %}}
      </tbody>
      <tfoot><tr style="background:#fde8e8;font-weight:bold;"><td style="padding:2mm;">Total Deductions</td><td style="padding:2mm;text-align:right;">₹ {{{{ total_deductions }}}}</td></tr></tfoot>
    </table>
  </div>
  <div style="background:#1a3a6b;color:#fff;padding:3mm 4mm;font-size:10pt;font-weight:bold;margin-top:3mm;border-radius:1mm;">
    Net Pay: ₹ {{{{ net_salary }}}} &nbsp;({{{{ net_salary_words }}}})
  </div>
</div>
""")

_PAYSLIP_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#0f2027,#203a43);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:5mm;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:12pt;font-weight:bold;">{{{{ school_name }}}}</div>
        <div style="font-size:7.5pt;color:#aad4e0;">{{{{ school_address }}}}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:10pt;font-weight:bold;color:#64d8f0;">PAYSLIP</div>
        <div style="font-size:8pt;">{{{{ pay_month }}}} {{{{ pay_year }}}}</div>
      </div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4mm;margin-bottom:5mm;font-size:9pt;">
    <div style="background:#f0f4f8;padding:3mm;border-radius:2mm;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Employee</div>
      <strong>{{{{ staff_name }}}}</strong><br/>{{{{ designation }}}} | {{{{ department }}}}<br/>
      EMP: {{{{ employee_id }}}} | PAN: {{{{ pan_number }}}}
    </div>
    <div style="background:#f0f4f8;padding:3mm;border-radius:2mm;font-size:9pt;">
      <div style="font-size:7pt;color:#666;text-transform:uppercase;margin-bottom:1mm;">Attendance</div>
      Days Worked: <strong>{{{{ days_worked }}}} / {{{{ total_days }}}}</strong><br/>
      Bank A/C: {{{{ bank_account }}}}<br/>PF: {{{{ pf_number }}}}
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4mm;margin-bottom:3mm;">
    <table style="border-collapse:collapse;font-size:8.5pt;">
      <thead><tr style="background:#203a43;color:#fff;"><th style="padding:2mm;text-align:left;" colspan="2">Earnings</th></tr></thead>
      <tbody>{{% for e in earnings %}}<tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ e.component }}}}</td><td style="padding:2mm;text-align:right;">₹{{{{ e.amount }}}}</td></tr>{{% endfor %}}</tbody>
      <tfoot><tr style="font-weight:bold;background:#e8f4fd;"><td style="padding:2mm;">Gross</td><td style="padding:2mm;text-align:right;">₹{{{{ gross_salary }}}}</td></tr></tfoot>
    </table>
    <table style="border-collapse:collapse;font-size:8.5pt;">
      <thead><tr style="background:#7b1a1a;color:#fff;"><th style="padding:2mm;text-align:left;" colspan="2">Deductions</th></tr></thead>
      <tbody>{{% for d in deductions %}}<tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ d.component }}}}</td><td style="padding:2mm;text-align:right;">₹{{{{ d.amount }}}}</td></tr>{{% endfor %}}</tbody>
      <tfoot><tr style="font-weight:bold;background:#fde8e8;"><td style="padding:2mm;">Total</td><td style="padding:2mm;text-align:right;">₹{{{{ total_deductions }}}}</td></tr></tfoot>
    </table>
  </div>
  <div style="background:#203a43;color:#fff;padding:3mm 5mm;border-radius:2mm;font-size:10pt;font-weight:bold;">
    Net Pay: ₹ {{{{ net_salary }}}} &nbsp;<span style="font-size:8pt;color:#aad4e0;">({{{{ net_salary_words }}}})</span>
  </div>
</div>
""")

_PAYSLIP_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}border-top:1mm solid #333;">
  <div style="margin-bottom:5mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:9pt;">Salary Slip – {{{{ pay_month }}}} {{{{ pay_year }}}}</div>
  </div>
  <div style="border:0.3mm solid #ddd;padding:3mm;margin-bottom:4mm;font-size:9pt;">
    <strong>{{{{ staff_name }}}}</strong> | {{{{ designation }}}} | Dept: {{{{ department }}}} | EMP: {{{{ employee_id }}}} | Days: {{{{ days_worked }}}}/{{{{ total_days }}}}
  </div>
  <div style="display:flex;gap:6mm;">
    <table style="flex:1;border-collapse:collapse;font-size:9pt;">
      <thead><tr><th style="padding:2mm;border-bottom:0.5mm solid #333;text-align:left;">Earnings</th><th style="padding:2mm;border-bottom:0.5mm solid #333;">Amt</th></tr></thead>
      <tbody>{{% for e in earnings %}}<tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ e.component }}}}</td><td style="padding:2mm;text-align:right;">₹{{{{ e.amount }}}}</td></tr>{{% endfor %}}</tbody>
      <tfoot><tr style="font-weight:bold;border-top:0.5mm solid #333;"><td style="padding:2mm;">Gross</td><td style="padding:2mm;text-align:right;">₹{{{{ gross_salary }}}}</td></tr></tfoot>
    </table>
    <table style="flex:1;border-collapse:collapse;font-size:9pt;">
      <thead><tr><th style="padding:2mm;border-bottom:0.5mm solid #333;text-align:left;">Deductions</th><th style="padding:2mm;border-bottom:0.5mm solid #333;">Amt</th></tr></thead>
      <tbody>{{% for d in deductions %}}<tr style="border-bottom:0.2mm solid #eee;"><td style="padding:2mm;">{{{{ d.component }}}}</td><td style="padding:2mm;text-align:right;">₹{{{{ d.amount }}}}</td></tr>{{% endfor %}}</tbody>
      <tfoot><tr style="font-weight:bold;border-top:0.5mm solid #333;"><td style="padding:2mm;">Total</td><td style="padding:2mm;text-align:right;">₹{{{{ total_deductions }}}}</td></tr></tfoot>
    </table>
  </div>
  <div style="font-size:10pt;font-weight:bold;margin-top:3mm;padding:2mm 0;border-top:0.5mm solid #333;">
    Net Pay: ₹ {{{{ net_salary }}}} ({{{{ net_salary_words }}}})
  </div>
</div>
""")

# --- Custom ---
_CUSTOM_CLASSIC = _doctype(f"""
<div style="{_A4_STYLE}border:0.5mm solid #333;">
  <div style="text-align:center;margin-bottom:8mm;">
    <div style="font-size:14pt;font-weight:bold;color:#1a3a6b;">{{{{ school_name }}}}</div>
    <div style="font-size:8.5pt;color:#555;">{{{{ school_address }}}}</div>
    <div style="font-size:12pt;font-weight:bold;margin-top:3mm;color:#1a3a6b;">{{{{ document_title }}}}</div>
  </div>
  <div style="font-size:10pt;line-height:2.0;text-align:justify;">{{{{ document_body }}}}</div>
  <div style="margin-top:14mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Authorised Signatory</div></div>
  </div>
</div>
""")

_CUSTOM_MODERN = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="background:linear-gradient(90deg,#1a3a6b,#2c5364);color:#fff;padding:5mm 8mm;border-radius:2mm;margin-bottom:8mm;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:10pt;color:#64d8f0;margin-top:2mm;">{{{{ document_title }}}}</div>
  </div>
  <div style="font-size:10pt;line-height:2.0;text-align:justify;color:#222;">{{{{ document_body }}}}</div>
  <div style="margin-top:14mm;text-align:right;font-size:9pt;">
    <div style="display:inline-block;text-align:center;">
      <div style="border-top:0.3mm solid #333;width:45mm;margin:0 auto;"></div>
      <div>Authorised Signatory</div>
      <div style="font-size:8pt;color:#666;">Date: {{{{ issue_date }}}}</div>
    </div>
  </div>
</div>
""")

_CUSTOM_MINIMAL = _doctype(f"""
<div style="{_A4_STYLE}">
  <div style="border-bottom:0.5mm solid #333;padding-bottom:4mm;margin-bottom:6mm;text-align:center;">
    <div style="font-size:13pt;font-weight:bold;">{{{{ school_name }}}}</div>
    <div style="font-size:11pt;font-weight:bold;margin-top:2mm;">{{{{ document_title }}}}</div>
  </div>
  <div style="font-size:10.5pt;line-height:2.0;text-align:justify;">{{{{ document_body }}}}</div>
  <div style="margin-top:14mm;display:flex;justify-content:space-between;font-size:9pt;">
    <div>Date: {{{{ issue_date }}}}</div>
    <div style="text-align:center;"><div style="border-top:0.3mm solid #333;width:40mm;"></div><div>Authorised Signatory</div></div>
  </div>
</div>
""")

# ---------------------------------------------------------------------------
# Master list: DEFAULT DOCUMENT TEMPLATES
# (template_name, template_type, canvas_w, canvas_h, html, is_default)
# canvas sizes: ID cards = 85.6×54mm, A4 half = 210×148mm, A4 = 210×297mm
# ---------------------------------------------------------------------------

DEFAULT_DOCUMENT_TEMPLATES: list[dict] = [
    # student_id_front
    {"template_name": "Student ID Front – Classic",  "template_type": "student_id_front",  "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_FRONT_CLASSIC,  "layout_json": None, "is_default": True},
    {"template_name": "Student ID Front – Modern",   "template_type": "student_id_front",  "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_FRONT_MODERN,   "layout_json": None, "is_default": False},
    {"template_name": "Student ID Front – Minimal",  "template_type": "student_id_front",  "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_FRONT_MINIMAL,  "layout_json": None, "is_default": False},
    # student_id_back
    {"template_name": "Student ID Back – Classic",   "template_type": "student_id_back",   "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_BACK_CLASSIC,   "layout_json": None, "is_default": True},
    {"template_name": "Student ID Back – Modern",    "template_type": "student_id_back",   "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_BACK_MODERN,    "layout_json": None, "is_default": False},
    {"template_name": "Student ID Back – Minimal",   "template_type": "student_id_back",   "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STUDENT_ID_BACK_MINIMAL,   "layout_json": None, "is_default": False},
    # staff_id_front
    {"template_name": "Staff ID Front – Classic",    "template_type": "staff_id_front",    "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_FRONT_CLASSIC,    "layout_json": None, "is_default": True},
    {"template_name": "Staff ID Front – Modern",     "template_type": "staff_id_front",    "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_FRONT_MODERN,     "layout_json": None, "is_default": False},
    {"template_name": "Staff ID Front – Minimal",    "template_type": "staff_id_front",    "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_FRONT_MINIMAL,    "layout_json": None, "is_default": False},
    # staff_id_back
    {"template_name": "Staff ID Back – Classic",     "template_type": "staff_id_back",     "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_BACK_CLASSIC,     "layout_json": None, "is_default": True},
    {"template_name": "Staff ID Back – Modern",      "template_type": "staff_id_back",     "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_BACK_MODERN,      "layout_json": None, "is_default": False},
    {"template_name": "Staff ID Back – Minimal",     "template_type": "staff_id_back",     "canvas_width_mm": 85.6, "canvas_height_mm": 54.0,  "template_html": _STAFF_ID_BACK_MINIMAL,     "layout_json": None, "is_default": False},
    # admit_card
    {"template_name": "Admit Card – Classic",        "template_type": "admit_card",        "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _ADMIT_CARD_CLASSIC,        "layout_json": None, "is_default": True},
    {"template_name": "Admit Card – Modern",         "template_type": "admit_card",        "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _ADMIT_CARD_MODERN,         "layout_json": None, "is_default": False},
    {"template_name": "Admit Card – Minimal",        "template_type": "admit_card",        "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _ADMIT_CARD_MINIMAL,        "layout_json": None, "is_default": False},
    # fee_receipt
    {"template_name": "Fee Receipt – Classic",       "template_type": "fee_receipt",       "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _FEE_RECEIPT_CLASSIC,       "layout_json": None, "is_default": True},
    {"template_name": "Fee Receipt – Modern",        "template_type": "fee_receipt",       "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _FEE_RECEIPT_MODERN,        "layout_json": None, "is_default": False},
    {"template_name": "Fee Receipt – Minimal",       "template_type": "fee_receipt",       "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _FEE_RECEIPT_MINIMAL,       "layout_json": None, "is_default": False},
    # report_card
    {"template_name": "Report Card – Classic",       "template_type": "report_card",       "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _REPORT_CARD_CLASSIC,       "layout_json": None, "is_default": True},
    {"template_name": "Report Card – Modern",        "template_type": "report_card",       "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _REPORT_CARD_MODERN,        "layout_json": None, "is_default": False},
    {"template_name": "Report Card – Minimal",       "template_type": "report_card",       "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _REPORT_CARD_MINIMAL,       "layout_json": None, "is_default": False},
    # transfer_certificate
    {"template_name": "Transfer Certificate – Classic",  "template_type": "transfer_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _TC_CLASSIC,  "layout_json": None, "is_default": True},
    {"template_name": "Transfer Certificate – Modern",   "template_type": "transfer_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _TC_MODERN,   "layout_json": None, "is_default": False},
    {"template_name": "Transfer Certificate – Minimal",  "template_type": "transfer_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _TC_MINIMAL,  "layout_json": None, "is_default": False},
    # bonafide_certificate
    {"template_name": "Bonafide Certificate – Classic",  "template_type": "bonafide_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _BONAFIDE_CLASSIC,  "layout_json": None, "is_default": True},
    {"template_name": "Bonafide Certificate – Modern",   "template_type": "bonafide_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _BONAFIDE_MODERN,   "layout_json": None, "is_default": False},
    {"template_name": "Bonafide Certificate – Minimal",  "template_type": "bonafide_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _BONAFIDE_MINIMAL,  "layout_json": None, "is_default": False},
    # character_certificate
    {"template_name": "Character Certificate – Classic",  "template_type": "character_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CHAR_CERT_CLASSIC,  "layout_json": None, "is_default": True},
    {"template_name": "Character Certificate – Modern",   "template_type": "character_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CHAR_CERT_MODERN,   "layout_json": None, "is_default": False},
    {"template_name": "Character Certificate – Minimal",  "template_type": "character_certificate",  "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CHAR_CERT_MINIMAL,  "layout_json": None, "is_default": False},
    # payslip
    {"template_name": "Payslip – Classic",           "template_type": "payslip",           "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _PAYSLIP_CLASSIC,           "layout_json": None, "is_default": True},
    {"template_name": "Payslip – Modern",            "template_type": "payslip",           "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _PAYSLIP_MODERN,            "layout_json": None, "is_default": False},
    {"template_name": "Payslip – Minimal",           "template_type": "payslip",           "canvas_width_mm": 210.0, "canvas_height_mm": 148.0, "template_html": _PAYSLIP_MINIMAL,           "layout_json": None, "is_default": False},
    # custom
    {"template_name": "Custom Document – Classic",   "template_type": "custom",            "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CUSTOM_CLASSIC,            "layout_json": None, "is_default": True},
    {"template_name": "Custom Document – Modern",    "template_type": "custom",            "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CUSTOM_MODERN,             "layout_json": None, "is_default": False},
    {"template_name": "Custom Document – Minimal",   "template_type": "custom",            "canvas_width_mm": 210.0, "canvas_height_mm": 297.0, "template_html": _CUSTOM_MINIMAL,            "layout_json": None, "is_default": False},
]


# ---------------------------------------------------------------------------
# DEFAULT NOTIFICATION TEMPLATES
# 8 triggers × 3 styles (Formal / Friendly / Brief) = 24 templates
# Fields: name, event_trigger, channel, subject, body_template, is_active, is_default
# ---------------------------------------------------------------------------

DEFAULT_NOTIFICATION_TEMPLATES: list[dict] = [

    # ── attendance_absent ──────────────────────────────────────────────────
    {
        "name": "Attendance Absent – Formal",
        "event_trigger": "attendance_absent",
        "channel": "in_app,email",
        "subject": "Absence Notification – {student_name}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "This is to inform you that your ward {student_name} of Class {class_name} – {section_name} "
            "was marked absent on {date}.\n\n"
            "If this absence was pre-approved, please disregard this message. "
            "Otherwise, kindly ensure regular attendance.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Attendance Absent – Friendly",
        "event_trigger": "attendance_absent",
        "channel": "in_app,sms",
        "subject": "We missed {student_name} today!",
        "body_template": (
            "Hi! 👋 Just letting you know that {student_name} (Class {class_name}) "
            "was absent today, {date}. Hope everything is okay! "
            "Contact us if you need anything. – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Attendance Absent – Brief",
        "event_trigger": "attendance_absent",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: {student_name} (Cl {class_name}) absent on {date}. "
            "Call {school_phone} for info."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── fee_due ────────────────────────────────────────────────────────────
    {
        "name": "Fee Due – Formal",
        "event_trigger": "fee_due",
        "channel": "in_app,email",
        "subject": "Fee Payment Reminder – {student_name}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "This is a reminder that a fee of ₹{amount} is due for {student_name} "
            "(Class {class_name}) by {due_date}.\n\n"
            "Kindly make the payment at the earliest to avoid any late charges.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Fee Due – Friendly",
        "event_trigger": "fee_due",
        "channel": "in_app,sms",
        "subject": "Friendly Fee Reminder for {student_name}",
        "body_template": (
            "Hi! A quick reminder that ₹{amount} in fees for {student_name} is due by {due_date}. "
            "Please pay at your earliest convenience. Thank you! – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Fee Due – Brief",
        "event_trigger": "fee_due",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: Fee ₹{amount} due for {student_name} by {due_date}. "
            "Pay now to avoid penalty."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── fee_receipt ────────────────────────────────────────────────────────
    {
        "name": "Fee Receipt – Formal",
        "event_trigger": "fee_receipt",
        "channel": "in_app,email",
        "subject": "Fee Payment Confirmed – Receipt #{receipt_number}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "We acknowledge receipt of ₹{amount} paid on {payment_date} towards the fee account of "
            "{student_name} (Class {class_name}). Receipt No: {receipt_number}.\n\n"
            "Thank you for the timely payment.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Fee Receipt – Friendly",
        "event_trigger": "fee_receipt",
        "channel": "in_app,sms",
        "subject": "Payment Received! 🎉",
        "body_template": (
            "Great news! Payment of ₹{amount} for {student_name} was received on {payment_date}. "
            "Receipt #{receipt_number}. Thank you! – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Fee Receipt – Brief",
        "event_trigger": "fee_receipt",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: ₹{amount} received for {student_name} on {payment_date}. "
            "Rcpt#{receipt_number}."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── result_published ───────────────────────────────────────────────────
    {
        "name": "Result Published – Formal",
        "event_trigger": "result_published",
        "channel": "in_app,email",
        "subject": "Exam Results Published – {exam_name}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "The results for {exam_name} have been published for {student_name} "
            "(Class {class_name} – {section_name}).\n\n"
            "Please log in to the school portal to view the detailed report card.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Result Published – Friendly",
        "event_trigger": "result_published",
        "channel": "in_app,push",
        "subject": "📊 Results are out for {student_name}!",
        "body_template": (
            "Hi! The {exam_name} results for {student_name} are now available. "
            "Log in to the portal to check the report card. – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Result Published – Brief",
        "event_trigger": "result_published",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: {exam_name} results published for {student_name}. "
            "Check portal for details."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── homework_assigned ──────────────────────────────────────────────────
    {
        "name": "Homework Assigned – Formal",
        "event_trigger": "homework_assigned",
        "channel": "in_app,email",
        "subject": "Homework Assigned – {subject_name}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "Homework has been assigned in {subject_name} for {student_name} "
            "(Class {class_name} – {section_name}) by {teacher_name}.\n\n"
            "Title: {homework_title}\nDue Date: {due_date}\n\n"
            "Please ensure timely completion.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Homework Assigned – Friendly",
        "event_trigger": "homework_assigned",
        "channel": "in_app,push",
        "subject": "📚 New Homework: {homework_title}",
        "body_template": (
            "Hey! New homework in {subject_name} for {student_name}: \"{homework_title}\" "
            "due on {due_date}. Let's get it done! – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Homework Assigned – Brief",
        "event_trigger": "homework_assigned",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: HW assigned – {subject_name} ({homework_title}). "
            "Due: {due_date}. Student: {student_name}."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── ptm_reminder ───────────────────────────────────────────────────────
    {
        "name": "PTM Reminder – Formal",
        "event_trigger": "ptm_reminder",
        "channel": "in_app,email",
        "subject": "Parent-Teacher Meeting Reminder",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "This is a reminder that the Parent-Teacher Meeting for {student_name} "
            "(Class {class_name} – {section_name}) is scheduled on {ptm_date} at {ptm_time}.\n\n"
            "Venue: {ptm_venue}\n\n"
            "Please ensure your presence.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "PTM Reminder – Friendly",
        "event_trigger": "ptm_reminder",
        "channel": "in_app,push",
        "subject": "📅 PTM Reminder for {student_name}",
        "body_template": (
            "Hi! Don't forget – the Parent-Teacher Meeting for {student_name} is on {ptm_date} at {ptm_time}, "
            "{ptm_venue}. We look forward to seeing you! – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "PTM Reminder – Brief",
        "event_trigger": "ptm_reminder",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: PTM for {student_name} on {ptm_date} at {ptm_time}, {ptm_venue}."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── birthday ───────────────────────────────────────────────────────────
    {
        "name": "Birthday Wish – Formal",
        "event_trigger": "birthday",
        "channel": "in_app,email",
        "subject": "Birthday Greetings from {school_name}",
        "body_template": (
            "Dear {student_name},\n\n"
            "On behalf of the entire {school_name} family, we wish you a very Happy Birthday!\n\n"
            "May this special day bring you joy, happiness, and success in all your endeavours.\n\n"
            "Best Wishes,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Birthday Wish – Friendly",
        "event_trigger": "birthday",
        "channel": "in_app,push",
        "subject": "🎂 Happy Birthday, {student_name}!",
        "body_template": (
            "Happy Birthday, {student_name}! 🎉🎂 "
            "Wishing you a fantastic day filled with fun and smiles. "
            "From all of us at {school_name}!"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Birthday Wish – Brief",
        "event_trigger": "birthday",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "Happy Birthday {student_name}! 🎂 Best wishes from {school_name}."
        ),
        "is_active": True,
        "is_default": False,
    },

    # ── custom ─────────────────────────────────────────────────────────────
    {
        "name": "Custom Notice – Formal",
        "event_trigger": "custom",
        "channel": "in_app,email",
        "subject": "{notice_subject}",
        "body_template": (
            "Dear Parent/Guardian,\n\n"
            "{notice_body}\n\n"
            "For any queries, please contact {school_phone}.\n\n"
            "Regards,\n{school_name}"
        ),
        "is_active": True,
        "is_default": True,
    },
    {
        "name": "Custom Notice – Friendly",
        "event_trigger": "custom",
        "channel": "in_app,push",
        "subject": "📢 {notice_subject}",
        "body_template": (
            "Hi! {notice_body} "
            "Feel free to reach us at {school_phone}. – {school_name}"
        ),
        "is_active": True,
        "is_default": False,
    },
    {
        "name": "Custom Notice – Brief",
        "event_trigger": "custom",
        "channel": "sms",
        "subject": None,
        "body_template": (
            "{school_name}: {notice_body}"
        ),
        "is_active": True,
        "is_default": False,
    },
]
