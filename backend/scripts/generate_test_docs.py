"""Generate 5 real Chinese NDA PDFs and upload them to the backend."""
import os, sys, json, shutil
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import http.client

# ── Font ──
FONT = "Helvetica"
for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(fp):
        try: pdfmetrics.registerFont(TTFont("CN", fp)); FONT = "CN"; break
        except: pass

# ── 5 NDA Documents ──
DOCS = [
    ("供应商保密协议", [
        ("保密义务", "接收方同意对披露方的保密信息予以严格保密。未经披露方事先书面同意，不得向任何第三方披露、泄露或允许使用保密信息。接收方应采取不低于保护自身同类保密信息的谨慎程度来保护披露方的保密信息。"),
        ("保密期限", "本协议项下的保密义务自披露之日起持续有效五年。期限届满后，接收方应返还或销毁所有包含保密信息的材料及其副本。构成商业秘密的保密信息，保密义务在相关信息进入公有领域前持续有效。"),
        ("例外情形", "以下信息不属于保密信息：披露时已为公众所知；非因接收方过错成为公众所知；接收方在披露前已合法持有且有书面记录证明；接收方从有权披露的第三方合法获取。"),
        ("违约救济", "接收方违反保密义务的，披露方有权要求立即停止违约行为、消除影响并赔偿全部损失。损失难以计算的，违约金不低于人民币壹佰万元整。"),
        ("存续条款", "本协议终止或到期后，保密义务、违约救济和争议解决条款应继续有效。保密信息的返还或销毁不影响上述条款的存续效力。"),
        ("管辖法律", "本协议的订立、效力、解释、履行及争议解决均适用中华人民共和国法律。"),
        ("争议解决", "因本协议引起的任何争议，双方应首先友好协商。协商不成的，任何一方有权向披露方所在地有管辖权的人民法院提起诉讼。"),
        ("通知条款", "所有通知应以书面形式发出，通过专人递送、挂号信、电子邮件或传真方式发送至对方在本协议中列明的地址。"),
        ("可转让性", "未经披露方事先书面同意，接收方不得将其在本协议项下的任何权利或义务转让给任何第三方。"),
        ("完整协议", "本协议构成双方就保密事宜达成的完整协议，取代双方此前就同一事项达成的所有口头或书面约定。"),
    ]),
    ("技术合作保密协议", [
        ("保密义务", "双方就技术合作项目交换的全部技术资料、商业计划、客户信息及其他非公开信息均构成保密信息。双方均应采取合理措施保护对方保密信息的安全性。"),
        ("保密期限", "保密期限为自签署之日起八年。涉及核心技术的保密信息保密义务永久有效。期限届满后三十日内各方应书面确认已履行信息返还或销毁义务。"),
        ("例外情形", "保密义务不适用于：披露时已进入公有领域的信息；接收方能证明在披露前已独立开发的信息；根据法律法规或司法机关强制要求必须披露的信息。"),
        ("违约救济", "违约方应停止侵害、消除影响、赔礼道歉并赔偿损失。实际损失难以计算的，赔偿金额按违约方因违约获得的利益确定。"),
        ("存续条款", "保密义务、违约救济条款和争议解决条款在协议终止后继续有效，不因合作项目的终止或变更而受到影响。"),
        ("管辖法律", "本协议适用中华人民共和国法律。解释条款时应遵循诚实信用原则和商业惯例。"),
        ("争议解决", "争议应友好协商解决，协商期限三十日。协商不成的，提交中国国际经济贸易仲裁委员会按其仲裁规则仲裁。"),
        ("通知条款", "通知应以书面形式发送至对方首页载明的地址。地址变更应立即通知。以下列方式送达时间最早的为准。"),
        ("可转让性", "任何一方不得未经对方书面同意转让本协议项下的权利义务。因合并、分立产生的承继除外。"),
        ("完整协议", "本协议与附件共同构成完整约定。不一致的以附件为准。修改须经双方授权代表签署书面文件。"),
    ]),
    ("员工保密与知识产权协议", [
        ("保密义务", "员工在职期间及离职后，对工作中接触到的公司商业秘密、技术秘密、经营信息、客户资料等负有保密义务。不得以任何方式向任何第三方泄露。"),
        ("保密期限", "保密义务自入职之日起持续至离职后三年。涉及核心商业秘密的，保密义务持续至该信息进入公有领域为止。离职时须签署保密承诺确认书。"),
        ("例外情形", "不在保密范围：员工通过公开渠道获取的行业通用知识；员工在公司工作前已掌握且有明确记录证明的技术；法律法规要求必须披露但员工已事先通知公司的信息。"),
        ("违约救济", "员工违反保密义务的，公司有权解除劳动合同并要求赔偿直接和间接经济损失。赔偿包括调查费用、律师费用和商业损失。情节严重的依法追究刑事责任。"),
        ("知识产权归属", "员工在职期间完成的与公司业务相关的所有发明创造、技术方案、软件代码、设计方案等知识产权均归公司所有。"),
        ("竞业限制", "员工离职后两年内，不得直接或间接在与公司存在竞争关系的企业任职。履行竞业限制期间公司按月支付补偿金。"),
        ("管辖法律", "本协议的解释和适用适用中华人民共和国法律。任何条款被认定无效的不影响其他条款的效力。"),
        ("争议解决", "劳动争议应先通过公司内部申诉机制处理。处理不成的，可向劳动争议仲裁委员会申请仲裁。"),
        ("资料归还", "员工离职时应归还全部公司资料、设备、文件和存储介质，不得以任何形式保留复制件。"),
        ("完整协议", "本协议是劳动合同的组成部分，与劳动合同具有同等法律效力。不一致的以保护公司利益的条款为准。"),
    ]),
    ("战略合作框架保密协议", [
        ("保密义务", "基于双方战略合作框架，各方对合作过程中获悉的对方商业计划、财务数据、技术路线、用户数据和市场策略予以最高级别保密。未经对方书面授权不得对外公开合作内容。"),
        ("保密期限", "保密期限为自信息接收之日起十年。战略合作终止后保密义务继续有效。保密信息持有人应在合作终止后六十日内返还或销毁全部保密资料。"),
        ("例外情形", "不视为违反保密义务：信息已由披露方自行公开；根据证券交易所规则必须披露但事先协商了披露范围和内容；向已签署保密承诺的审计机构披露。"),
        ("违约救济", "战略合作层面的保密违约将导致严重的商业信誉损害。违约方除承担实际损失赔偿外，还应支付违约金人民币伍佰万元并公开致歉。"),
        ("存续条款", "保密义务、赔偿条款和数据安全条款在协议终止后无限期有效。战略合作关系的终止不影响上述条款的持续适用。"),
        ("数据安全", "双方应遵守个人信息保护法和数据安全法。涉及用户数据共享的应事先取得用户明示同意并确保数据转移过程的安全性。"),
        ("管辖法律", "本协议适用中华人民共和国法律。履行协议时应遵循诚信和公平交易原则。"),
        ("争议解决", "双方应尽最大努力协商解决争议。协商无法解决的任何一方可向协议签署地人民法院提起诉讼。"),
        ("通知条款", "战略层面通知应采用书面形式并加盖公章。紧急通知可通过电子邮件发出但应在三个工作日内以书面形式确认。"),
        ("完整协议", "本协议是战略合作的基石文件。后续签署的单项合作协议与本协议冲突的以本协议为准。修订需经双方董事会批准。"),
    ]),
    ("投资尽职调查保密协议", [
        ("保密义务", "投资方及其聘请的中介机构在尽职调查过程中获取的全部信息均为保密信息。投资方应确保所有信息接收方签署不低于本协议标准的保密承诺。"),
        ("保密期限", "尽职调查信息保密期限为自信息提供之日起三年。投资交易未达成的投资方应在决定不投资后三十日内销毁或返还全部保密资料并书面确认。"),
        ("例外情形", "可使用保密信息：投资方内部投决会审议，参会成员知晓保密义务；向有限合伙人报告但已脱敏处理；法律法规或监管机构要求。"),
        ("不招揽义务", "投资方在尽职调查期间及终止后两年内，不得直接或间接招揽目标公司的核心管理人员、技术人员和关键销售人员。"),
        ("不竞争承诺", "投资方在尽职调查期间不得使用所获信息从事与目标公司业务竞争的活动。商业计划被用于竞争目的的投资方承担全部法律责任。"),
        ("违约救济", "投资方违反保密义务将严重影响市场声誉。违约赔偿包括实际损失、预期利益损失和法律费用。违约金为人民币叁佰万元。"),
        ("管辖法律", "本协议适用中华人民共和国法律。协议中的不安条款按照行业惯例进行合理解释。"),
        ("争议解决", "争议首先协商解决，期限不超过二十个工作日。协商不成的任何一方可向投资方所在地人民法院提起诉讼。"),
        ("通知条款", "所有通知应同时发送至对方指定联系人和备份联系人。投资方通知应同时抄送目标公司指定的外部律师。"),
        ("完整协议", "本协议取代双方此前关于保密事宜的全部口头和书面沟通。可与投资条款清单并存，保密条款方面以本协议为准。"),
    ]),
]


def make_pdf(clauses, path):
    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=30*mm, bottomMargin=25*mm, leftMargin=25*mm, rightMargin=25*mm)
    ts = ParagraphStyle("T", fontName=FONT, fontSize=18, leading=26, spaceAfter=10*mm, alignment=TA_CENTER)
    hs = ParagraphStyle("H", fontName=FONT, fontSize=13, leading=18, spaceBefore=5*mm, spaceAfter=2*mm)
    bs = ParagraphStyle("B", fontName=FONT, fontSize=11, leading=17, spaceBefore=2*mm, spaceAfter=2*mm, firstLineIndent=22)

    story = [Paragraph("保密协议", ts), Spacer(1, 5*mm)]
    nums = ["一","二","三","四","五","六","七","八","九","十"]
    for i, (t, c) in enumerate(clauses):
        story.append(Paragraph(f"第{nums[i]}条  {t}", hs))
        story.append(Paragraph(c, bs))

    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("本协议一式两份，双方各执一份，具有同等法律效力。", bs))
    doc.build(story)


def upload(title, pdf_path):
    """Upload via pure Python http.client (avoid subprocess encoding issues)."""
    BOUNDARY = b"----FormBoundary7MA4YWxkTrZu0gW"

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    fname = os.path.basename(pdf_path)

    body = b""
    # file field
    body += b"--" + BOUNDARY + b"\r\n"
    body += b'Content-Disposition: form-data; name="file"; filename="document.pdf"\r\n'
    body += b"Content-Type: application/pdf\r\n\r\n"
    body += pdf_data + b"\r\n"
    # title field
    body += b"--" + BOUNDARY + b"\r\n"
    body += b'Content-Disposition: form-data; name="title"\r\n\r\n'
    body += title.encode("utf-8") + b"\r\n"
    # document_type
    body += b"--" + BOUNDARY + b"\r\n"
    body += b'Content-Disposition: form-data; name="document_type"\r\n\r\n'
    body += b"NDA\r\n"
    body += b"--" + BOUNDARY + b"--\r\n"

    headers = {
        "Authorization": "Bearer dev-token",
        "Content-Type": f"multipart/form-data; boundary={BOUNDARY.decode()}",
    }

    conn = http.client.HTTPConnection("localhost", 8000, timeout=60)
    conn.request("POST", "/api/v1/documents/upload", body=body, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    return data


def start_review(doc_id):
    conn = http.client.HTTPConnection("localhost", 8000, timeout=60)
    headers = {
        "Authorization": "Bearer dev-token",
        "Content-Type": "application/json",
    }
    conn.request("POST", f"/api/v1/documents/{doc_id}/review", body=b"{}", headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read())
    conn.close()
    return data


if __name__ == "__main__":
    out = Path("storage/test_docs")
    out.mkdir(parents=True, exist_ok=True)

    for i, (title, clauses) in enumerate(DOCS):
        path = out / f"{i+1:02d}-{title}.pdf"
        sys.stdout.write(f"[{i+1}/5] {title} ... ")
        sys.stdout.flush()

        make_pdf(clauses, path)
        sys.stdout.write(f"PDF={path.stat().st_size}B ")

        r = upload(title, str(path))
        if r.get("code") == 0:
            did = r["data"]["document_id"]
            sys.stdout.write(f"upload={did} ")
            r2 = start_review(did)
            if r2.get("code") == 0:
                print(f"review={r2['data']['status']}")
            else:
                print(f"review-FAIL: {r2}")
        else:
            print(f"UPLOAD-FAIL: {r}")

    print(f"\nDone - {len(DOCS)} documents with mock AI review")
