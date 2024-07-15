import logging
import sys
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime

from docx.opc.exceptions import PackageNotFoundError
from docxtpl import DocxTemplate
from linkedin_api import Linkedin
from linkedin_api.client import ChallengeException

from universities import search_university, get_universities_list
from websites import convert_url

# %% Constants.
parser = ArgumentParser()
parser.add_argument("--username", type=str, required=True,
                    help="Username of the user's LinkedIn account.")
parser.add_argument("--password", type=str, required=True,
                    help="Password of the user's LinkedIn account, corresponding to \""
                         "linkedin_username\".")
parser.add_argument('--profile_id', type=str, required=True,
                    help="The value {linkedin_profile_id} matches the user's LinkedIn "
                         "profile https://www.linkedin.com/in/{linkedin_profile_id}/")
parser.add_argument('--output_path', type=str, required=True,
                    help="Filepath to save the generated resume.")
parser.add_argument('--template_path', type=str, default="resume_template.docx",
                    help="Filepath of resume template.")
cmd, _ = parser.parse_known_args()

# %% Set logging.
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# %% Get Linkedin profile.
logging.info("Start to visit Linkedin profile.")
try:
    api = Linkedin(cmd.username, cmd.password)
except ChallengeException:
    logging.error("Possible reasons: (1) Linkedin username and password don't match. "
                  "(2) reCAPTCHA is required.")
    exit(0)
profile = api.get_profile(cmd.profile_id)
contact = api.get_profile_contact_info(cmd.profile_id)
logging.info("Finish to visit Linkedin profile.")

# %% contact information
first_name = profile.get('firstName', '')
last_name = profile.get('lastName', '')
city_name = profile.get('geoLocationName', '')
country_name = profile.get('geoCountryName', '')
telephones = contact.get("phone_numbers", [])
if len(telephones) > 0:
    telephone = telephones[0].get("number", "")
else:
    telephone = ""
websites = []
for website in contact.get("websites", []):
    domain_name, domain_user = convert_url(website.get("url", ""))
    websites.append({"domain": domain_name, "user": domain_user})


# %% education
def get_year_month(dict_):
    default_date = {"month": "", "year": ""}
    default_time_period = {"startDate": default_date, "endDate": default_date}
    start_date = (dict_.get("timePeriod", default_time_period)
                  .get("startDate", default_date))
    start_year = start_date.get('year', '')
    start_month = start_date.get('month', '')
    start_dash = "-" if start_year or start_month else ""
    start_year_month_ = f"{start_year}{start_dash}{start_month}"
    end_date = (dict_.get("timePeriod", default_time_period)
                .get("endDate", default_date))
    end_year = end_date.get('year', '')
    end_month = end_date.get('month', '')
    end_dash = "-" if end_year or end_month else ""
    end_year_month_ = f"{end_year}{end_dash}{end_month}"
    return start_year_month_, end_year_month_


educations = []
universities_list = get_universities_list()
for education in profile.get("education", []):
    school_name = education.get("schoolName", "")
    degree_name = education.get("degreeName", "")
    start_year_month, end_year_month = get_year_month(education)
    school_info = search_university(school_name, universities_list)
    school_country = school_info.get("country", "")
    educations.append({
        "school_name": school_name,
        "country": school_country,
        "start_month": start_year_month,
        "end_month": end_year_month,
        "degree_name": degree_name,
    })


# %% publication


# Bullet point: https://github.com/elapouya/python-docx-template/issues/73
def get_key_points(dict_):
    key_points = []
    for item_text in dict_.get("description", "").split("\n"):
        if len(item_text) == 0:
            continue
        if item_text[0] in ("*", "•", "-", "+"):
            is_bullet = True
            item_text = item_text[1:].strip()
        else:
            is_bullet = False
        key_points.append({"bullet": is_bullet, "text": item_text})
    return key_points


publications = []
for publication in profile.get("publications", []):
    try:
        publication_date = datetime(**publication.get("date", {}))
        publication_date_str = publication_date.strftime("%Y-%m-%d")
    except TypeError:
        publication_date_str = ""
    publications.append({
        "title": publication.get("name", ""),
        "date": publication_date_str,
        "journal": publication.get("publisher", ""),
        "key_points": get_key_points(publication),
    })

# %% work experience
companies = defaultdict(list)
for work_experience in profile.get("experience", []):
    if "companyName" in work_experience:
        companies[work_experience["companyName"]].append(work_experience)
works = []
for company_name, roles in companies.items():
    roles_ = []
    for role in roles:
        start_year_month, end_year_month = get_year_month(role)
        roles_.append({
            "title": role.get("title", ""),
            "start_month": start_year_month,
            "end_month": end_year_month,
            "location": role.get("geoLocationName", ""),
            "key_points": get_key_points(role),
        })
    works.append({"name": company_name, "roles": roles_})

# %% honors and awards, certificates
honors = []
for honor in profile.get("honors", []):
    honor_year = honor.get("issueDate", {}).get("year", "")
    honor_month = honor.get("issueDate", {}).get("month", "")
    honors.append({
        "title": honor.get("title", ""),
        "month": f"{honor_year}-{honor_month}",
        "issued_by": honor.get("issuer", ""),
    })
certificates_unordered = []
for certificate in profile.get("certifications", []):
    start_year_month, _ = get_year_month(certificate)
    ordered_year_month = certificate.get("timePeriod", {}).get(
        "startDate", {})
    certificates_unordered.append({
        "ordered_key": (ordered_year_month.get("year", 0),
                        ordered_year_month.get("month", 0)),
        "title": certificate.get("name", ""),
        "month": start_year_month,
        "license_number": certificate.get("licenseNumber", ""),
        "issued_by": certificate.get("company", {}).get("name", ""),
    })
certificates = sorted(certificates_unordered,
                      key=lambda x: x["ordered_key"], reverse=True)

# %% volunteering
volunteers = []
for role in profile.get("volunteer", []):
    start_year_month, end_year_month = get_year_month(role)
    volunteers.append({
        "title": role.get("role", ""),
        "start_month": start_year_month,
        "end_month": end_year_month,
        "company_name": role.get("companyName", ""),
        "key_points": get_key_points(role),
    })

# %% context dictionary
email = contact.get("email_address", "")
context = {
    "name": f"{first_name} {last_name}",
    "about": profile.get("summary", ""),
    "title": profile.get("headline", ""),
    "telephone": telephone,
    "city": f"{city_name}, {country_name}",
    "email": "" if email is None else email,
    "linkedin": cmd.profile_id,
    "websites": websites,
    "educations": educations,
    "publications": publications,
    "works": works,
    "honors": honors,
    "certificates": certificates,
    "volunteers": volunteers,
}

# %% Render.
resume = DocxTemplate(cmd.template_path)
# If template is not valid: PackageNotFoundError
try:
    resume.render(context)
except PackageNotFoundError:
    logging.error("The resume template is invalid.")
    exit(0)
for paragraph in resume.paragraphs:  # remove empty paragraphs
    if len(paragraph.text) == 0:
        p = paragraph._element
        p.getparent().remove(p)
        p._p = p._element = None
resume.save(cmd.output_path)
