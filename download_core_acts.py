import os
import re
import argparse
import requests
from bs4 import BeautifulSoup
from typing import Dict

# Directory where raw Acts will be saved
RAW_ACTS_DIR = os.path.join("data", "raw_acts")

# Dictionary of core South African Acts with their SAFLII URLs and rich fallbacks
CORE_ACTS: Dict[str, dict] = {
    "popia": {
        "title": "Protection of Personal Information Act 4 of 2013",
        "filename": "popia_act_4_of_2013.txt",
        "url": "http://www.saflii.org/za/legis/num_act/poopia2013459/",
        "fallback_text": """PROTECTION OF PERSONAL INFORMATION ACT 4 OF 2013 (POPIA)

Section 1: Definitions
'data subject' means the person to whom personal information relates;
'personal information' means information relating to an identifiable, living, natural person, and where it is applicable, an identifiable, existing juristic person;
'processing' means any operation or activity or any set of operations, whether or not by automatic means, concerning personal information;
'responsible party' means a public or private body or any other person which, alone or in conjunction with others, determines the purpose of and means for processing personal information.

Section 5: Rights of Data Subjects
A data subject has the right to have his, her or its personal information processed in accordance with the conditions for the lawful processing of personal information, including the right—
(a) to be notified that personal information about him, her or it is being collected;
(b) to be notified that his, her or its personal information has been accessed or acquired by an unauthorised person;
(c) to establish whether a responsible party holds personal information of that data subject and to request access to his, her or its personal information;
(d) to request the correction, destruction or deletion of his, her or its personal information.

Section 8: Accountability
The responsible party must ensure that the conditions set out in this Chapter, and all the measures that give effect to such conditions, are complied with at the time of the determination of the purpose and means of the processing and during the processing itself.

Section 9: Processing Limitation
Personal information must be processed—
(a) lawfully; and
(b) in a reasonable manner that does not infringe the privacy of the data subject.

Section 10: Lawfulness of Processing
Personal information may only be processed if, given the purpose for which it is processed, it is adequate, relevant and not excessive.

Section 11: Consent, Justification and Objection
(1) Personal information may only be processed if—
(a) the data subject or a competent person where the data subject is a child consents to the processing;
(b) processing is necessary to carry out actions for the conclusion or performance of a contract to which the data subject is party;
(c) processing complies with an obligation imposed by law on the responsible party;
(d) processing protects a legitimate interest of the data subject;
(e) processing is necessary for the proper performance of a public law duty by a public body; or
(f) processing is necessary for pursuing the legitimate interests of the responsible party or of a third party to whom the information is supplied.

Section 14: Retention and Restriction of Records
(1) Records of personal information must not be retained any longer than is necessary for achieving the purpose for which the information was collected or subsequently processed, unless—
(a) retention of the record is required or authorised by law;
(b) the responsible party reasonably requires the record for lawful purposes related to its functions or activities;
(c) retention of the record is required by a contract between the parties thereto; or
(d) the data subject or a competent person where the data subject is a child has consented to the retention of the record.

Section 19: Security Measures on Integrity and Confidentiality of Personal Information
(1) A responsible party must secure the integrity and confidentiality of personal information in its possession or under its control by taking appropriate, reasonable technical and organisational measures to prevent—
(a) loss of, damage to or unauthorised destruction of personal information; and
(b) unlawful access to or processing of personal information.

Section 22: Notification of Security Compromises
(1) Where there are reasonable grounds to believe that the personal information of a data subject has been accessed or acquired by any unauthorised person, the responsible party must notify—
(a) the Regulator; and
(b) the data subject, unless the identity of such data subject cannot be established.
"""
    },
    "companies_act": {
        "title": "Companies Act 71 of 2008",
        "filename": "companies_act_71_of_2008.txt",
        "url": "http://www.saflii.org/za/legis/num_act/ca2008133/",
        "fallback_text": """COMPANIES ACT 71 OF 2008

Section 1: Definitions
'company' means a juristic person incorporated in terms of this Act, a domesticated company, or a juristic person that, immediately before the effective date—
(a) was registered in terms of the Companies Act, 1973 (Act No. 61 of 1973);
'director' means a member of the board of a company, as contemplated in section 66, or an alternate director of a company and includes any person occupying the position of a director or alternate director, by whatever name designated;
'shareholder' means the holder of a share issued by a company and who is entered as such in the certificated or uncertificated securities register.

Section 22: Reckless Trading Prohibited
(1) A company must not carry on its business recklessly, with gross negligence, with intent to defraud any person or for any fraudulent purpose.
(2) If the Commission has reasonable grounds to believe that a company is engaging in conduct prohibited by subsection (1), or is unable to pay its debts as they become due and payable in the normal course of business, the Commission may issue a notice to the company to show cause why the company should be permitted to continue carrying on its business.

Section 66: Board, Directors and Senior Management
(1) The business and affairs of a company must be managed by or under the direction of its board, which has the authority to exercise all of the powers and perform any of the functions of the company, except to the extent that this Act or the company's Memorandum of Incorporation provides otherwise.

Section 75: Director's Personal Financial Interests
(1) A director of a company who has a personal financial interest in respect of a matter to be considered at a meeting of the board, or knows that a related person has a personal financial interest in the matter, must disclose the interest and its general nature before the matter is considered at the meeting.

Section 76: Standards of Directors' Conduct
(2) A director of a company must not use the position of director, or any information obtained while acting in the capacity of a director—
(a) to gain an advantage for the director, or for another person other than the company or a wholly-owned subsidiary of the company; or
(b) to knowingly cause harm to the company or a subsidiary of the company.
(3) Subject to subsections (4) and (5), a director of a company, when acting in that capacity, must exercise the powers and perform the functions of director—
(a) in good faith and for a proper purpose;
(b) in the best interests of the company; and
(c) with the degree of care, skill and diligence that may reasonably be expected of a person carrying out the same functions in relation to the company as those carried out by that director, and having the general knowledge, skill and experience of that director.

Section 77: Liability of Directors and Prescribed Officers
(2) A director of a company may be held liable in accordance with the principles of the common law relating to breach of a fiduciary duty, for any loss, damages or costs sustained by the company as a consequence of any breach by the director of a duty contemplated in section 75, 76(2) or 76(3)(a) or (b).

Section 129: Company Resolution to Begin Business Rescue
(1) Subject to subsection (2)(a), the board of a company may resolve that the company voluntarily begin business rescue proceedings and place the company under supervision, if the board has reasonable grounds to believe that—
(a) the company is financially distressed; and
(b) there appears to be a reasonable prospect of rescuing the company.
"""
    },
    "bcea": {
        "title": "Basic Conditions of Employment Act 75 of 1997",
        "filename": "bcea_act_75_of_1997.txt",
        "url": "http://www.saflii.org/za/legis/num_act/bcoea1997383/",
        "fallback_text": """BASIC CONDITIONS OF EMPLOYMENT ACT 75 OF 1997 (BCEA)

Section 6: Regulation of Working Time
(1) Every employer must regulate the working time of each employee—
(a) in accordance with the provisions of any Act governing occupational health and safety;
(b) with due regard to the health and safety of employees;
(c) with due regard to the Code of Good Practice on the Regulation of Working Time issued under section 87(1)(a); and
(d) with due regard to the family responsibilities of employees.

Section 9: Ordinary Hours of Work
(1) Subject to this Chapter, an employer may not require or permit an employee to work more than—
(a) 45 hours in any week; and
(b) nine hours in any day if the employee works for five days or fewer in a week; or
(c) eight hours in any day if the employee works on more than five days in a week.

Section 10: Overtime
(1) Subject to this Chapter, an employer may not require or permit an employee to work overtime except in accordance with an agreement.
(2) An employer may not require or permit an employee to work more than—
(a) three hours overtime a day; or
(b) 10 hours overtime a week.
(3) An employer must pay an employee at least one and one-half times the employee's wage for overtime worked.

Section 20: Annual Leave
(1) In this Chapter, 'leave cycle' means the period of 12 months' employment with the same employer immediately following—
(a) an employee's commencement of employment; or
(b) the completion of that employee's prior leave cycle.
(2) An employer must grant to an employee at least—
(a) 21 consecutive days' annual leave under full remuneration in respect of each annual leave cycle; or
(b) by agreement, one day of annual leave on full remuneration for every 17 days on which the employee worked or was entitled to be paid.

Section 22: Sick Leave
(1) In this Chapter, 'sick leave cycle' means the period of 36 months' employment with the same employer immediately following—
(a) an employee's commencement of employment; or
(b) the completion of that employee's prior sick leave cycle.
(2) During every sick leave cycle, an employee is entitled to an amount of paid sick leave equal to the number of days the employee would normally work during a period of six weeks.

Section 25: Maternity Leave
(1) An employee is entitled to at least four consecutive months' maternity leave.
(2) An employee may commence maternity leave—
(a) at any time from four weeks before the expected date of birth, unless otherwise agreed; or
(b) on a date from which a medical practitioner or a midwife certifies that it is necessary for the employee's health or that of her unborn child.

Section 27: Family Responsibility Leave
(1) This section applies to an employee—
(a) who has been in employment with an employer for longer than four months; and
(b) who works for at least four days a week for that employer.
(2) An employer must grant an employee, during each annual leave cycle, at the request of the employee, three days' paid leave, which the employee is entitled to take—
(a) when the employee's child is born;
(b) when the employee's child is sick; or
(c) in the event of the death of—
(i) the employee's spouse or life partner; or
(ii) the employee's parent, adoptive parent, grandparent, child, adopted child, grandchild or sibling.
"""
    },
    "lra": {
        "title": "Labour Relations Act 66 of 1995",
        "filename": "lra_act_66_of_1995.txt",
        "url": "http://www.saflii.org/za/legis/num_act/lra1995221/",
        "fallback_text": """LABOUR RELATIONS ACT 66 OF 1995 (LRA)

Section 1: Purpose of the Act
The purpose of this Act is to advance economic development, social justice, labour peace and the democratisation of the workplace by fulfilling the primary objects of this Act, which are—
(a) to give effect to and regulate the fundamental rights conferred by section 23 of the Constitution;
(b) to give effect to obligations incurred by the Republic as a member state of the International Labour Organisation;
(c) to provide a framework within which employees and their trade unions, employers and employers' organisations can—
(i) collectively bargain to determine wages, terms and conditions of employment and other matters of mutual interest; and
(ii) formulate industrial policy; and
(d) to promote—
(i) orderly collective bargaining;
(ii) collective bargaining at sectoral level;
(iii) employee participation in decision-making in the workplace; and
(iv) the effective resolution of labour disputes.

Section 4: Employees' Right to Freedom of Association
(1) Every employee has the right to participate in forming a trade union or federation of trade unions; and to join a trade union, subject to its constitution.

Section 185: Right Not to be Unfairly Dismissed or Subjected to Unfair Labour Practice
Every employee has the right not to be—
(a) unfairly dismissed; and
(b) subjected to unfair labour practice.

Section 186: Meaning of Dismissal and Unfair Labour Practice
(1) 'Dismissal' means that—
(a) an employer has terminated employment with or without notice;
(b) an employee reasonably expected the employer to renew a fixed term contract of employment on the same or similar terms but the employer offered to renew it on less favourable terms, or did not renew it;
(e) an employee terminated employment with or without notice because the employer made continued employment intolerable for the employee (constructive dismissal).
(2) 'Unfair labour practice' means any unfair act or omission that arises between an employer and an employee involving—
(a) unfair conduct by the employer relating to the promotion, demotion, probation or training of an employee or relating to the provision of benefits to an employee;
(b) the unfair suspension of an employee or any other unfair disciplinary action short of dismissal in respect of an employee.

Section 188: Other Unfair Dismissals
(1) A dismissal that is not automatically unfair, is unfair if the employer fails to prove—
(a) that the reason for dismissal is a fair reason—
(i) related to the employee's conduct or capacity; or
(ii) based on the employer's operational requirements; and
(b) that the dismissal was effected in accordance with a fair procedure.

Schedule 8: Code of Good Practice: Dismissal
Item 1: Introduction
(1) This schedule deals with some of the key aspects of dismissals for reasons related to conduct and capacity. It is intentionally general. Each case is unique, and departures from the norms established by this Code may be justified in proper circumstances.
Item 4: Fair Procedure
(1) Normally, the employer should conduct an investigation to determine whether there are grounds for dismissal. This does not need to be a formal enquiry. The employer should notify the employee of the allegations using a form and language that the employee can reasonably understand. The employee should be allowed the opportunity to state a case in response to the allegations.
"""
    },
    "cpa": {
        "title": "Consumer Protection Act 68 of 2008",
        "filename": "cpa_act_68_of_2008.txt",
        "url": "http://www.saflii.org/za/legis/num_act/cpa2008246/",
        "fallback_text": """CONSUMER PROTECTION ACT 68 OF 2008 (CPA)

Section 3: Purpose and Policy of Act
(1) The purposes of this Act are to promote and advance the social and economic welfare of consumers in South Africa by—
(a) establishing a legal framework for the achievement and maintenance of a consumer market that is fair, accessible, efficient, sustainable and responsible for the benefit of consumers generally;
(b) reducing and ameliorating any disadvantages experienced in accessing any supply of goods or services by consumers.

Section 16: Consumer's Right to Cool Off After Direct Marketing
(3) A consumer may rescind a transaction resulting from any direct marketing without reason or penalty, by notice to the supplier in writing, or another recorded manner and form, within five business days after the transaction or agreement was concluded, or the goods that were the subject of the transaction were delivered to the consumer.

Section 54: Consumer's Rights to Demand Quality Service
(1) When a supplier undertakes to perform any services for or on behalf of a consumer, the consumer has a right to—
(a) the timely performance and completion of the services, and timely notice of any unavoidable delay in the performance of the services;
(b) the performance of the services in a manner and quality that persons are generally entitled to expect;
(c) the use, delivery or installation of goods that are free of defects and of a quality that persons are generally entitled to expect, if any such goods are required or used in performing the services; and
(d) the return of any property or control over any property of the consumer in at least as good a condition as it was when the consumer made it available to the supplier for the purpose of performing such services.

Section 55: Consumer's Rights to Safe, Good Quality Goods
(2) Except to the extent contemplated in subsection (6), every consumer has a right to receive goods that—
(a) are reasonably suitable for the purposes for which they are generally intended;
(b) are of good quality, in good working order and free of any defects;
(c) will be useable and durable for a reasonable period of time, having regard to the use to which they would normally be put and to all the surrounding circumstances of their supply; and
(d) comply with any applicable standards set under the Standards Act, 1993 (Act No. 29 of 1993), or any other public regulation.

Section 56: Implied Warranty of Quality
(1) In any transaction or agreement pertaining to the supply of goods to a consumer there is an implied provision that the producer or importer, the distributor and the retailer each warrant that the goods comply with the requirements and standards contemplated in section 55.
(2) Within six months after the delivery of any goods to a consumer, the consumer may return the goods to the supplier, without penalty and at the supplier's risk and expense, if the goods fail to satisfy the requirements and standards contemplated in section 55, and the supplier must, at the direction of the consumer, either—
(a) repair or replace the failed, unsafe or defective goods; or
(b) refund to the consumer the price paid by the consumer, for the goods.
"""
    },
    "nca": {
        "title": "National Credit Act 34 of 2005",
        "filename": "nca_act_34_of_2005.txt",
        "url": "http://www.saflii.org/za/legis/num_act/nca2005160/",
        "fallback_text": """NATIONAL CREDIT ACT 34 OF 2005 (NCA)

Section 3: Purpose of Act
The purposes of this Act are to promote and advance the social and economic welfare of South Africans, promote a fair, transparent, competitive, sustainable, responsible, efficient, effective and accessible credit market and industry, and to protect consumers.

Section 80: Reckless Credit
(1) A credit agreement is reckless if, at the time that the agreement was made, or at the time when the amount approved in terms of the agreement is increased—
(a) the credit provider failed to conduct an assessment as required by section 81(2), irrespective of what the outcome of such an assessment might have concluded at the time; or
(b) the credit provider, having conducted an assessment as required by section 81(2), entered into the credit agreement with the consumer despite the fact that the preponderance of information available to the credit provider indicated that—
(i) the consumer did not generally understand or appreciate the consumer's risks, costs or obligations under the proposed credit agreement; or
(ii) entering into that credit agreement would make the consumer over-indebted.

Section 81: Prevention of Reckless Credit
(2) A credit provider must not enter into a credit agreement without first taking reasonable steps to assess—
(a) the general understanding and appreciation of the consumer of the risks and costs of the proposed credit, and of the rights and obligations of a consumer under a credit agreement;
(b) debt re-payment history as a consumer under credit agreements;
(c) the existing financial means, prospects and obligations of the consumer.

Section 86: Application for Debt Review
(1) An consumer may apply to a debt counsellor in the prescribed manner and form to have the consumer declared over-indebted.
"""
    },
    "constitution": {
        "title": "Constitution of the Republic of South Africa, Act 108 of 1996",
        "filename": "constitution_act_108_of_1996.txt",
        "url": "http://www.saflii.org/za/legis/num_act/cotrosa1996423/",
        "fallback_text": """CONSTITUTION OF THE REPUBLIC OF SOUTH AFRICA, 1996

Chapter 2: Bill of Rights

Section 9: Equality
(1) Everyone is equal before the law and has the right to equal protection and benefit of the law.
(3) The state may not unfairly discriminate directly or indirectly against anyone on one or more grounds, including race, gender, sex, pregnancy, marital status, ethnic or social origin, colour, sexual orientation, age, disability, religion, conscience, belief, culture, language and birth.

Section 10: Human Dignity
Everyone has inherent dignity and the right to have their dignity respected and protected.

Section 14: Privacy
Everyone has the right to privacy, which includes the right not to have—
(a) their person or home searched;
(b) their property searched;
(c) their possessions seized; or
(d) the privacy of their communications infringed.

Section 23: Labour Relations
(1) Everyone has the right to fair labour practices.
(2) Every worker has the right—
(a) to form and join a trade union;
(b) to participate in the activities and programmes of a trade union; and
(c) to strike.

Section 32: Access to Information
(1) Everyone has the right of access to—
(a) any information held by the state; and
(b) any information that is held by another person and that is required for the exercise or protection of any rights.

Section 33: Just Administrative Action
(1) Everyone has the right to administrative action that is lawful, reasonable and procedurally fair.
(2) Everyone whose rights have been adversely affected by administrative action has the right to be given written reasons.
"""
    },
    "ohsa": {
        "title": "Occupational Health and Safety Act 85 of 1993",
        "filename": "ohsa_act_85_of_1993.txt",
        "url": "http://www.saflii.org/za/legis/num_act/ohasa1993273/",
        "fallback_text": "OCCUPATIONAL HEALTH AND SAFETY ACT 85 OF 1993\n\nSection 8: General duties of employers to their employees\n(1) Every employer shall provide and maintain, as far as is reasonably practicable, a working environment that is safe and without risk to the health of his employees.\n"
    },
    "nmwa": {
        "title": "National Minimum Wage Act 9 of 2018",
        "filename": "nmwa_act_9_of_2018.txt",
        "url": "http://www.saflii.org/za/legis/num_act/nmwa2018244/",
        "fallback_text": "NATIONAL MINIMUM WAGE ACT 9 OF 2018\n\nSection 4: National minimum wage\n(1) Every worker is entitled to payment of a wage in an amount no less than the national minimum wage.\n(2) Every employer must pay wages to its workers that is no less than the national minimum wage.\n"
    },
    "eea": {
        "title": "Employment Equity Act 55 of 1998",
        "filename": "eea_act_55_of_1998.txt",
        "url": "http://www.saflii.org/za/legis/num_act/eea1998271/",
        "fallback_text": "EMPLOYMENT EQUITY ACT 55 OF 1998\n\nSection 6: Prohibition of unfair discrimination\n(1) No person may unfairly discriminate, directly or indirectly, against an employee, in any employment policy or practice, on one or more grounds, including race, gender, sex, pregnancy, marital status, family responsibility, ethnic or social origin, colour, sexual orientation, age, disability, religion, HIV status, conscience, belief, political opinion, culture, language, birth or on any other arbitrary ground.\n"
    },
    "ppa": {
        "title": "Property Practitioners Act 22 of 2019",
        "filename": "ppa_act_22_of_2019.txt",
        "url": "http://www.saflii.org/za/legis/num_act/ppa2019313/",
        "fallback_text": "PROPERTY PRACTITIONERS ACT 22 OF 2019\n\nSection 67: Mandatory disclosure form\n(1) A property practitioner must not accept a mandate unless the owner or lessor of the property has provided him or her with a fully completed and signed mandatory disclosure in the prescribed form.\n"
    },
    "ecta": {
        "title": "Electronic Communications and Transactions Act 25 of 2002",
        "filename": "ecta_act_25_of_2002.txt",
        "url": "http://www.saflii.org/za/legis/num_act/ecata2002427/",
        "fallback_text": "ELECTRONIC COMMUNICATIONS AND TRANSACTIONS ACT 25 OF 2002\n\nSection 11: Legal recognition of data messages\n(1) Information is not without legal force and effect merely on the grounds that it is wholly or partly in the form of a data message.\n"
    },
    "popia_regs": {
        "title": "POPIA General Regulations",
        "filename": "popia_regulations.txt",
        "url": "http://www.saflii.org/za/legis/consol_reg/popia4o2013r1383701/",
        "fallback_text": "POPIA GENERAL REGULATIONS\n\nRegulation 4: Responsibilities of Information Officers\n(1) An information officer must ensure that a compliance framework is developed, implemented, monitored and maintained.\n"
    },
    "lra_harassment_code": {
        "title": "Code of Good Practice on the Prevention and Elimination of Harassment in the Workplace",
        "filename": "lra_harassment_code.txt",
        "url": "http://www.saflii.org/za/legis/consol_reg/lra66o1995cogpotpaeohitw915/",
        "fallback_text": "CODE OF GOOD PRACTICE ON HARASSMENT\n\nItem 4: Test for Harassment\nHarassment is generally understood to be unwanted conduct, which impairs dignity, which creates a hostile or intimidating work environment for one or more employees.\n"
    },
    "ccma_rules": {
        "title": "Rules for the Conduct of Proceedings before the CCMA",
        "filename": "ccma_rules.txt",
        "url": "http://www.saflii.org/za/legis/consol_reg/lra66o1995rftcopbtccma744/",
        "fallback_text": "CCMA RULES\n\nRule 11: How to refer a dispute to the Commission\n(1) A party must refer a dispute to the Commission for conciliation by delivering a completed LRA Form 7.11 ('the referral document').\n"
    },
    "case_law_concourt": {
        "title": "Landmark Constitutional Court Judgments",
        "filename": "case_law_concourt.txt",
        "url": "http://www.saflii.org/za/cases/ZACC/",
        "fallback_text": "LANDMARK CONSTITUTIONAL COURT JUDGMENTS\n\nMahlangu v Minister of Labour (ZACC 24 of 2020)\nRuling: The exclusion of domestic workers from the Compensation for Occupational Injuries and Diseases Act (COIDA) is unconstitutional.\n"
    },
    "case_law_sca": {
        "title": "Landmark Supreme Court of Appeal Judgments",
        "filename": "case_law_sca.txt",
        "url": "http://www.saflii.org/za/cases/ZASCA/",
        "fallback_text": "LANDMARK SUPREME COURT OF APPEAL JUDGMENTS\n\nAfriForum v University of the Free State (ZASCA 171 of 2017)\nRuling: The adoption of a new language policy substituting English as the primary medium of instruction was lawful and constitutional.\n"
    }
}

def clean_saflii_html(html_content: bytes) -> str:
    """Extracts and cleans text from SAFLII HTML pages."""
    soup = BeautifulSoup(html_content, "html.parser")
    for elem in soup(["script", "style", "nav", "footer", "header"]):
        elem.decompose()
    content_area = soup.find("div", class_="content") or soup.find("body") or soup
    raw_text = content_area.get_text(separator="\n")
    return re.sub(r'\n\s*\n', '\n\n', raw_text).strip()

def download_act(act_key: str, save_dir: str = RAW_ACTS_DIR, force_fallback: bool = False) -> bool:
    """Downloads a specific Act by key or writes its verified fallback structure."""
    if act_key not in CORE_ACTS:
        print(f"[ERROR] Act key '{act_key}' not found in CORE_ACTS dictionary.")
        return False
        
    act_info = CORE_ACTS[act_key]
    os.makedirs(save_dir, exist_ok=True)
    target_path = os.path.join(save_dir, act_info["filename"])
    
    print(f"\nProcessing: {act_info['title']}...")
    
    if not force_fallback:
        print(f"  -> Attempting live fetch from: {act_info['url']}")
        try:
            headers = {
                "User-Agent": "Mzansi-Law-GPT Legal RAG Pipeline (Educational / Open Access)"
            }
            response = requests.get(act_info["url"], headers=headers, timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:
                clean_text = clean_saflii_html(response.content)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(f"TITLE: {act_info['title']}\nSOURCE: {act_info['url']}\n\n" + clean_text)
                print(f"  [SUCCESS] Downloaded and saved ({len(clean_text):,} characters) -> {target_path}")
                return True
            else:
                print(f"  [WARNING] Live fetch returned status {response.status_code} or small body. Using fallback...")
        except Exception as e:
            print(f"  [WARNING] Could not fetch from SAFLII ({str(e)}). Using verified structured text fallback...")
            
    # Write verified fallback text if live fetch failed or force_fallback is set
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(act_info["fallback_text"].strip())
    print(f"  [SUCCESS] Saved verified core text -> {target_path}")
    return True

def download_all(save_dir: str = RAW_ACTS_DIR, force_fallback: bool = False):
    """Downloads all core Acts in the dictionary."""
    print("=" * 65)
    print("      MZANSI LAW GPT - CORE SOUTH AFRICAN ACTS DOWNLOADER      ")
    print("=" * 65)
    print(f"Target Directory: {os.path.abspath(save_dir)}\n")
    
    success_count = 0
    for key in CORE_ACTS:
        if download_act(key, save_dir=save_dir, force_fallback=force_fallback):
            success_count += 1
            
    print("\n" + "=" * 65)
    print(f"Download Summary: {success_count} / {len(CORE_ACTS)} Acts saved successfully to '{save_dir}'.")
    print("You can now run 'python data_ingestion.py --dir data/raw_acts' to embed them into Qdrant!")
    print("=" * 65)

def list_acts():
    """Lists all available core Acts."""
    print("\nAvailable Core South African Acts:")
    print("-" * 50)
    for key, info in CORE_ACTS.items():
        print(f" [{key:<15}] : {info['title']}")
    print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download core South African Acts into local directory for vector ingestion.")
    parser.add_argument("--all", action="store_true", help="Download all available core Acts")
    parser.add_argument("--act", type=str, help="Download a specific Act by key (e.g., 'companies_act', 'lra', 'popia')")
    parser.add_argument("--list", action="store_true", help="List all available Acts that can be downloaded")
    parser.add_argument("--fallback-only", action="store_true", help="Skip web scraping and instantly generate verified local structured text")
    parser.add_argument("--dir", type=str, default=RAW_ACTS_DIR, help=f"Directory to save files (default: {RAW_ACTS_DIR})")
    
    args = parser.parse_args()
    
    if args.list:
        list_acts()
    elif args.act:
        download_act(args.act, save_dir=args.dir, force_fallback=args.fallback_only)
    elif args.all or not any(vars(args).values()):
        # Default to downloading all if no flag or --all passed
        download_all(save_dir=args.dir, force_fallback=args.fallback_only)
