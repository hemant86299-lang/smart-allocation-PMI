/**
 * mockData.js
 * ---------------------------------------------------------------------------
 * Centralised demo dataset for the SmartAlloc frontend.
 *
 * All data on this file is SYNTHETIC and exists purely to demonstrate the UI.
 * The field names deliberately mirror the schema used by the Python engine in
 * `../../src` and `../../demoData/*.csv` so that this frontend can later be
 * pointed at the real pipeline output with minimal changes:
 *
 *   candidates.csv  -> candidate_id, name, category, location_pref,
 *                      skills, qualification_score
 *   internships.csv -> internship_id, title, location, capacity,
 *                      required_skills, reserved_category
 *
 * Extra presentation-only fields (college, education, preferredRoles, ...)
 * are added so the dashboard looks like a real allocation portal.
 * ---------------------------------------------------------------------------
 */

export const SCHEME_META = {
  title: 'AI-Based Smart Allocation Engine',
  subtitle: 'PM Internship Scheme',
  cycle: 'Allocation Cycle 2026-A',
  ministry: 'Ministry of Corporate Affairs',
  mode: 'Demo Mode',
}

/** Hard eligibility thresholds — mirrors src/eligibility.py */
export const ELIGIBILITY_RULES = {
  minQualificationScore: 55,
  requireLocationMatch: true,
  minSkillOverlap: 1,
}

/** Match-score weights used by the demo scoring engine (utils/allocationEngine.js) */
export const SCORE_WEIGHTS = {
  skill: 40,
  education: 20,
  location: 15,
  preference: 15,
  eligibility: 10,
}

export const LOCATIONS = [
  'Delhi',
  'Noida',
  'Gurugram',
  'Bengaluru',
  'Hyderabad',
  'Mumbai',
  'Pune',
  'Chennai',
  'Jaipur',
  'Lucknow',
]

export const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'EWS']

export const SKILLS = [
  'Python',
  'Java',
  'C++',
  'SQL',
  'Excel',
  'Data Science',
  'Data Analysis',
  'Machine Learning',
  'Web Development',
  'React',
  'JavaScript',
  'Cloud Computing',
  'Cybersecurity',
  'Networking',
  'Linux',
  'UI/UX Design',
  'Business Analytics',
  'Financial Analysis',
  'Digital Marketing',
  'Communication',
  'Embedded Systems',
]

export const EDUCATION_LEVELS = [
  'B.Tech (CSE)',
  'B.Tech (IT)',
  'B.Tech (ECE)',
  'B.Tech (Mechanical)',
  'BCA',
  'MCA',
  'M.Tech',
  'B.Sc',
  'M.Sc',
  'B.Com',
  'BBA',
  'MBA',
  'B.Des',
]

export const SECTORS = [
  'Information Technology',
  'Banking & Finance',
  'Public Sector (PSU)',
  'E-Commerce',
  'Telecom',
  'Manufacturing',
  'Consulting',
  'Defence & Aerospace',
]

/* ========================================================================== */
/* INTERNSHIP OPPORTUNITIES                                                    */
/* ========================================================================== */

export const opportunities = [
  {
    id: 'I001',
    company: 'Infosys Limited',
    role: 'Software Development Intern',
    location: 'Bengaluru',
    sector: 'Information Technology',
    requiredSkills: ['Java', 'Python', 'SQL'],
    capacity: 6,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 12000,
    durationMonths: 6,
    description:
      'Work with product engineering squads on backend services, REST modules and database layers for enterprise banking clients.',
    postedOn: '2026-06-18',
  },
  {
    id: 'I002',
    company: 'Tata Consultancy Services',
    role: 'Data Analyst Intern',
    location: 'Mumbai',
    sector: 'Information Technology',
    requiredSkills: ['SQL', 'Excel', 'Data Analysis'],
    capacity: 5,
    reservedCategory: 'OBC',
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 11000,
    durationMonths: 6,
    description:
      'Build operational dashboards, run cohort analysis and support reporting automation for the retail analytics practice.',
    postedOn: '2026-06-20',
  },
  {
    id: 'I003',
    company: 'Wipro Technologies',
    role: 'Machine Learning Intern',
    location: 'Hyderabad',
    sector: 'Information Technology',
    requiredSkills: ['Python', 'Machine Learning', 'Data Science'],
    capacity: 4,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 70,
    stipend: 15000,
    durationMonths: 6,
    description:
      'Assist the AI lab in feature engineering, model evaluation and deployment of forecasting models on client datasets.',
    postedOn: '2026-06-22',
  },
  {
    id: 'I004',
    company: 'HCLTech',
    role: 'Web Development Intern',
    location: 'Noida',
    sector: 'Information Technology',
    requiredSkills: ['Web Development', 'React', 'JavaScript'],
    capacity: 6,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 10000,
    durationMonths: 5,
    description:
      'Develop responsive front-end modules and component libraries for internal digital transformation platforms.',
    postedOn: '2026-06-25',
  },
  {
    id: 'I005',
    company: 'Bharat Electronics Limited',
    role: 'Cybersecurity Intern',
    location: 'Delhi',
    sector: 'Defence & Aerospace',
    requiredSkills: ['Cybersecurity', 'Networking', 'Linux'],
    capacity: 3,
    reservedCategory: 'SC',
    minQualificationScore: 55,
    matchThreshold: 65,
    stipend: 14000,
    durationMonths: 6,
    description:
      'Support the security operations centre with vulnerability assessment, log review and hardening of internal Linux systems.',
    postedOn: '2026-06-26',
  },
  {
    id: 'I006',
    company: 'Deloitte India',
    role: 'Business Analytics Intern',
    location: 'Gurugram',
    sector: 'Consulting',
    requiredSkills: ['Business Analytics', 'Excel', 'SQL'],
    capacity: 5,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 16000,
    durationMonths: 6,
    description:
      'Contribute to client diagnostics, KPI modelling and market-sizing studies for the strategy & analytics practice.',
    postedOn: '2026-06-28',
  },
  {
    id: 'I007',
    company: 'Zoho Corporation',
    role: 'UI/UX Design Intern',
    location: 'Chennai',
    sector: 'Information Technology',
    requiredSkills: ['UI/UX Design', 'Web Development', 'Communication'],
    capacity: 4,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 12500,
    durationMonths: 6,
    description:
      'Design wireframes, interaction flows and design-system components for SaaS products used by SMB customers.',
    postedOn: '2026-06-30',
  },
  {
    id: 'I008',
    company: 'Paytm (One97 Communications)',
    role: 'Cloud Infrastructure Intern',
    location: 'Noida',
    sector: 'Banking & Finance',
    requiredSkills: ['Cloud Computing', 'Python', 'Networking'],
    capacity: 4,
    reservedCategory: 'EWS',
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 18000,
    durationMonths: 6,
    description:
      'Automate deployment pipelines, monitor container workloads and assist with cost optimisation of cloud infrastructure.',
    postedOn: '2026-07-02',
  },
  {
    id: 'I009',
    company: 'NTPC Limited',
    role: 'Data Science Intern',
    location: 'Lucknow',
    sector: 'Public Sector (PSU)',
    requiredSkills: ['Data Science', 'Python', 'Excel'],
    capacity: 3,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 65,
    stipend: 13000,
    durationMonths: 6,
    description:
      'Analyse plant efficiency and load-forecast datasets to support the operations planning cell with predictive insights.',
    postedOn: '2026-07-04',
  },
  {
    id: 'I010',
    company: 'Flipkart Internet',
    role: 'Software Development Intern',
    location: 'Bengaluru',
    sector: 'E-Commerce',
    requiredSkills: ['C++', 'Java', 'SQL'],
    capacity: 4,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 65,
    stipend: 20000,
    durationMonths: 6,
    description:
      'Work on high-throughput order-management services, caching strategies and low-latency search components.',
    postedOn: '2026-07-06',
  },
  {
    id: 'I011',
    company: 'Reliance Jio Infocomm',
    role: 'Network Engineering Intern',
    location: 'Jaipur',
    sector: 'Telecom',
    requiredSkills: ['Networking', 'Communication', 'Python'],
    capacity: 3,
    reservedCategory: 'ST',
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 12000,
    durationMonths: 5,
    description:
      'Assist the regional NOC with fibre-rollout planning, link diagnostics and automation of routine network audits.',
    postedOn: '2026-07-08',
  },
  {
    id: 'I012',
    company: 'Mahindra & Mahindra',
    role: 'Embedded Systems Intern',
    location: 'Pune',
    sector: 'Manufacturing',
    requiredSkills: ['C++', 'Embedded Systems', 'Networking'],
    capacity: 4,
    reservedCategory: null,
    minQualificationScore: 55,
    matchThreshold: 60,
    stipend: 15000,
    durationMonths: 6,
    description:
      'Support firmware validation and CAN-bus diagnostics for next-generation electric vehicle control units.',
    postedOn: '2026-07-10',
  },
]

/* ========================================================================== */
/* CANDIDATES                                                                  */
/* ========================================================================== */

const c = (
  id,
  name,
  category,
  education,
  college,
  locationPref,
  altLocations,
  skills,
  qualificationScore,
  experienceMonths,
  preferredRoles,
  preferredSector,
  graduationYear = 2026
) => ({
  id,
  name,
  category,
  education,
  college,
  locationPref,
  altLocations,
  skills,
  qualificationScore,
  experienceMonths,
  preferredRoles,
  preferredSector,
  graduationYear,
  registrationNo: `PMIS/2026/${id.slice(1)}`,
  email: `${name.toLowerCase().replace(/[^a-z]+/g, '.')}@pmis.demo`,
  phone: `+91 98${id.slice(1)}0 ${41000 + Number(id.slice(1))}`,
  appliedOn: `2026-07-${String((Number(id.slice(1)) % 26) + 2).padStart(2, '0')}`,
})

export const candidates = [
  /* ---- Bengaluru ---- */
  c('C0001', 'Rahul Sharma', 'General', 'B.Tech (CSE)', 'NIT Kurukshetra', 'Bengaluru', ['Hyderabad', 'Pune'], ['Python', 'Java', 'C++', 'SQL'], 91.4, 6, ['Software Development Intern', 'Machine Learning Intern'], 'Information Technology'),
  c('C0002', 'Ananya Iyer', 'OBC', 'B.Tech (IT)', 'PES University', 'Bengaluru', ['Chennai'], ['Java', 'SQL', 'Web Development'], 84.2, 3, ['Software Development Intern', 'Web Development Intern'], 'Information Technology'),
  c('C0003', 'Karthik Reddy', 'General', 'MCA', 'Christ University', 'Bengaluru', ['Hyderabad'], ['Java', 'C++', 'SQL', 'Excel'], 78.6, 4, ['Software Development Intern'], 'E-Commerce'),
  c('C0004', 'Sneha Nair', 'EWS', 'B.Tech (CSE)', 'RV College of Engineering', 'Bengaluru', ['Pune'], ['Python', 'Machine Learning', 'SQL'], 88.9, 5, ['Machine Learning Intern', 'Data Science Intern'], 'Information Technology'),
  c('C0005', 'Aditya Menon', 'SC', 'B.Tech (ECE)', 'BMS College of Engineering', 'Bengaluru', ['Chennai'], ['C++', 'Python', 'Networking'], 71.3, 0, ['Embedded Systems Intern', 'Software Development Intern'], 'Manufacturing'),
  c('C0006', 'Pooja Deshpande', 'General', 'B.Sc', 'Bangalore University', 'Bengaluru', ['Mumbai'], ['Excel', 'Data Analysis', 'SQL'], 66.8, 2, ['Data Analyst Intern', 'Business Analytics Intern'], 'Consulting'),
  c('C0007', 'Vikram Singh', 'OBC', 'B.Tech (CSE)', 'Dayananda Sagar College', 'Bengaluru', ['Delhi'], ['Java', 'Web Development'], 59.4, 0, ['Web Development Intern'], 'Information Technology'),
  c('C0008', 'Nandini Rao', 'ST', 'B.Tech (IT)', 'Sir M. Visvesvaraya Institute of Technology', 'Bengaluru', ['Hyderabad'], ['Python', 'SQL'], 52.7, 0, ['Software Development Intern'], 'Information Technology', 2027),
  c('C0009', 'Harshit Jain', 'General', 'B.Tech (CSE)', 'IIIT Bangalore', 'Bengaluru', ['Hyderabad', 'Pune'], ['C++', 'Java', 'Python', 'Machine Learning', 'SQL'], 94.6, 12, ['Software Development Intern', 'Machine Learning Intern'], 'E-Commerce'),

  /* ---- Mumbai ---- */
  c('C0010', 'Priya Kulkarni', 'OBC', 'B.Com', 'Narsee Monjee College of Commerce', 'Mumbai', ['Pune'], ['Excel', 'SQL', 'Financial Analysis', 'Data Analysis'], 82.1, 3, ['Data Analyst Intern', 'Financial Analytics Intern'], 'Banking & Finance'),
  c('C0011', 'Rohan Patil', 'OBC', 'BBA', 'NMIMS Mumbai', 'Mumbai', ['Pune', 'Gurugram'], ['Excel', 'Business Analytics', 'Data Analysis'], 76.5, 2, ['Business Analytics Intern', 'Data Analyst Intern'], 'Consulting'),
  c('C0012', 'Zoya Shaikh', 'General', 'B.Sc', 'University of Mumbai', 'Mumbai', ['Pune'], ['Python', 'SQL', 'Data Science', 'Data Analysis'], 89.3, 6, ['Data Analyst Intern', 'Data Science Intern'], 'Information Technology'),
  c('C0013', 'Nikhil Joshi', 'EWS', 'B.Tech (IT)', 'VJTI Mumbai', 'Mumbai', ['Bengaluru'], ['Java', 'SQL', 'Web Development'], 85.7, 4, ['Software Development Intern', 'Data Analyst Intern'], 'Information Technology'),
  c('C0014', 'Meera Bhatt', 'OBC', 'MBA', 'Welingkar Institute of Management', 'Mumbai', ['Gurugram'], ['Excel', 'Financial Analysis', 'Communication'], 68.9, 8, ['Financial Analytics Intern', 'Data Analyst Intern'], 'Banking & Finance'),

  /* ---- Hyderabad ---- */
  c('C0015', 'Sai Krishna Varma', 'General', 'M.Tech', 'IIIT Hyderabad', 'Hyderabad', ['Bengaluru'], ['Python', 'Machine Learning', 'Data Science', 'SQL'], 95.8, 10, ['Machine Learning Intern', 'Data Science Intern'], 'Information Technology', 2025),
  c('C0016', 'Divya Prasad', 'SC', 'B.Tech (CSE)', 'Chaitanya Bharathi Institute of Technology', 'Hyderabad', ['Chennai'], ['Python', 'Machine Learning', 'Web Development'], 79.4, 3, ['Machine Learning Intern', 'Web Development Intern'], 'Information Technology'),
  c('C0017', 'Arjun Goud', 'OBC', 'B.Tech (CSE)', 'VNR VJIET', 'Hyderabad', ['Bengaluru'], ['Python', 'Data Science', 'Excel'], 73.2, 1, ['Data Science Intern', 'Machine Learning Intern'], 'Public Sector (PSU)'),
  c('C0018', 'Lakshmi Bandaru', 'ST', 'B.Sc', 'Osmania University', 'Hyderabad', ['Bengaluru'], ['Data Science', 'Excel', 'Data Analysis'], 64.5, 0, ['Data Science Intern', 'Data Analyst Intern'], 'Public Sector (PSU)'),
  c('C0019', 'Faizan Ahmed', 'EWS', 'B.Tech (IT)', 'MVSR Engineering College', 'Hyderabad', ['Mumbai'], ['Java', 'Web Development'], 57.1, 0, ['Web Development Intern'], 'Information Technology'),

  /* ---- Noida ---- */
  c('C0020', 'Ishaan Verma', 'General', 'B.Tech (CSE)', 'Amity University Noida', 'Noida', ['Delhi', 'Gurugram'], ['Web Development', 'React', 'JavaScript', 'Python'], 87.6, 8, ['Web Development Intern', 'Software Development Intern'], 'Information Technology'),
  c('C0021', 'Tanya Gupta', 'EWS', 'B.Tech (IT)', 'Jaypee Institute of Information Technology', 'Noida', ['Delhi'], ['Cloud Computing', 'Python', 'Web Development'], 83.4, 5, ['Cloud Infrastructure Intern', 'Web Development Intern'], 'Banking & Finance'),
  c('C0022', 'Mohit Chauhan', 'EWS', 'BCA', 'GL Bajaj Institute of Technology', 'Noida', ['Delhi'], ['Networking', 'Cloud Computing', 'Communication'], 69.8, 2, ['Cloud Infrastructure Intern', 'Network Engineering Intern'], 'Telecom'),
  c('C0023', 'Simran Kaur', 'General', 'B.Tech (CSE)', 'Galgotias University', 'Noida', ['Gurugram'], ['React', 'Web Development', 'UI/UX Design'], 80.2, 4, ['Web Development Intern', 'UI/UX Design Intern'], 'Information Technology'),
  c('C0024', 'Abhishek Yadav', 'OBC', 'MCA', 'Sharda University', 'Noida', ['Delhi', 'Lucknow'], ['Java', 'Web Development', 'SQL'], 74.9, 3, ['Web Development Intern', 'Software Development Intern'], 'Information Technology'),
  c('C0025', 'Neha Bansal', 'General', 'B.Tech (IT)', 'Amity University Noida', 'Noida', ['Gurugram', 'Delhi'], ['JavaScript', 'React', 'Web Development', 'Python'], 91.2, 7, ['Web Development Intern', 'UI/UX Design Intern'], 'Information Technology'),
  c('C0026', 'Sameer Khan', 'EWS', 'B.Tech (ECE)', 'IIMT College of Engineering', 'Noida', ['Delhi'], ['Networking', 'Python', 'C++'], 61.3, 0, ['Cloud Infrastructure Intern', 'Network Engineering Intern'], 'Telecom'),
  c('C0027', 'Ritu Saxena', 'SC', 'BCA', 'IEC College of Engineering', 'Noida', ['Lucknow'], ['Web Development', 'Excel'], 56.8, 0, ['Web Development Intern'], 'Information Technology', 2027),

  /* ---- Delhi ---- */
  c('C0028', 'Aman Chauhan', 'SC', 'B.Tech (CSE)', 'Delhi Technological University', 'Delhi', ['Noida', 'Gurugram'], ['Cybersecurity', 'Networking', 'Linux', 'Python'], 86.3, 6, ['Cybersecurity Intern', 'Network Engineering Intern'], 'Defence & Aerospace'),
  c('C0029', 'Kavya Malhotra', 'SC', 'B.Tech (IT)', 'Netaji Subhas University of Technology', 'Delhi', ['Noida'], ['Cybersecurity', 'Networking', 'Python'], 81.7, 4, ['Cybersecurity Intern', 'Cloud Infrastructure Intern'], 'Defence & Aerospace'),
  c('C0030', 'Rajat Khanna', 'General', 'B.Tech (CSE)', 'IIIT Delhi', 'Delhi', ['Gurugram', 'Noida'], ['Cybersecurity', 'Linux', 'C++', 'Python'], 93.1, 9, ['Cybersecurity Intern', 'Software Development Intern'], 'Defence & Aerospace'),
  c('C0031', 'Deepa Rani', 'SC', 'BCA', 'Jamia Millia Islamia', 'Delhi', ['Noida'], ['Networking', 'Communication', 'Excel'], 63.4, 1, ['Network Engineering Intern', 'Cybersecurity Intern'], 'Telecom'),
  c('C0032', 'Yash Chopra', 'OBC', 'B.Tech (ECE)', 'Maharaja Agrasen Institute of Technology', 'Delhi', ['Noida'], ['Networking', 'C++'], 70.6, 0, ['Network Engineering Intern', 'Embedded Systems Intern'], 'Telecom'),

  /* ---- Gurugram ---- */
  c('C0033', 'Aarav Malik', 'General', 'BBA', 'Amity University Gurugram', 'Gurugram', ['Delhi', 'Noida'], ['Business Analytics', 'Excel', 'SQL', 'Data Analysis'], 84.8, 5, ['Business Analytics Intern', 'Data Analyst Intern'], 'Consulting'),
  c('C0034', 'Riya Sethi', 'OBC', 'B.Com', 'Shri Ram College of Commerce', 'Gurugram', ['Delhi'], ['Excel', 'Financial Analysis', 'Business Analytics'], 79.3, 3, ['Business Analytics Intern', 'Financial Analytics Intern'], 'Banking & Finance'),
  c('C0035', 'Kunal Ahuja', 'General', 'MBA', 'MDI Gurgaon', 'Gurugram', ['Delhi', 'Mumbai'], ['Business Analytics', 'SQL', 'Python', 'Excel'], 88.1, 14, ['Business Analytics Intern'], 'Consulting', 2025),
  c('C0036', 'Shreya Kapoor', 'EWS', 'B.Sc', 'Ansal University', 'Gurugram', ['Delhi'], ['Excel', 'Data Analysis', 'Communication'], 72.4, 2, ['Data Analyst Intern', 'Business Analytics Intern'], 'Consulting'),
  c('C0037', 'Tarun Bhatia', 'General', 'B.Tech (CSE)', 'The NorthCap University', 'Gurugram', ['Noida'], ['SQL', 'Python', 'Web Development'], 65.9, 1, ['Software Development Intern', 'Business Analytics Intern'], 'Information Technology'),

  /* ---- Chennai ---- */
  c('C0038', 'Aishwarya Subramanian', 'General', 'B.Des', 'SRM Institute of Science and Technology', 'Chennai', ['Bengaluru'], ['UI/UX Design', 'Web Development', 'Communication'], 87.2, 6, ['UI/UX Design Intern'], 'Information Technology'),
  c('C0039', 'Vignesh Balaji', 'OBC', 'B.Tech (IT)', 'Anna University', 'Chennai', ['Bengaluru'], ['Web Development', 'React', 'UI/UX Design'], 78.8, 4, ['UI/UX Design Intern', 'Web Development Intern'], 'Information Technology'),
  c('C0040', 'Kritika Menon', 'General', 'B.Tech (CSE)', 'VIT Chennai', 'Chennai', ['Bengaluru', 'Hyderabad'], ['Web Development', 'Python', 'Communication'], 82.5, 3, ['Web Development Intern', 'UI/UX Design Intern'], 'Information Technology'),
  c('C0041', 'Surya Prakash', 'SC', 'BCA', 'Loyola College', 'Chennai', ['Bengaluru'], ['Communication', 'Excel', 'Digital Marketing'], 60.2, 0, ['Digital Marketing Intern', 'UI/UX Design Intern'], 'E-Commerce'),

  /* ---- Lucknow ---- */
  c('C0042', 'Ayush Tripathi', 'General', 'B.Tech (CSE)', 'IET Lucknow', 'Lucknow', ['Noida', 'Delhi'], ['Python', 'Data Science', 'SQL', 'Machine Learning'], 85.4, 5, ['Data Science Intern', 'Machine Learning Intern'], 'Public Sector (PSU)'),
  c('C0043', 'Sadhana Mishra', 'OBC', 'M.Sc', 'University of Lucknow', 'Lucknow', ['Delhi'], ['Data Science', 'Excel', 'Data Analysis'], 77.6, 2, ['Data Science Intern', 'Data Analyst Intern'], 'Public Sector (PSU)', 2025),
  c('C0044', 'Imran Siddiqui', 'EWS', 'B.Tech (IT)', 'Babu Banarasi Das University', 'Lucknow', ['Noida'], ['Python', 'Excel', 'Web Development'], 68.3, 1, ['Data Science Intern', 'Web Development Intern'], 'Information Technology'),

  /* ---- Jaipur ---- */
  c('C0045', 'Bhavesh Meena', 'ST', 'B.Tech (ECE)', 'MNIT Jaipur', 'Jaipur', ['Delhi', 'Gurugram'], ['Networking', 'Python', 'C++'], 80.9, 4, ['Network Engineering Intern', 'Embedded Systems Intern'], 'Telecom'),
  c('C0046', 'Sunita Bhil', 'ST', 'BCA', 'University of Rajasthan', 'Jaipur', ['Delhi'], ['Communication', 'Networking', 'Excel'], 62.7, 0, ['Network Engineering Intern'], 'Telecom'),
  c('C0047', 'Mayank Agarwal', 'General', 'B.Tech (CSE)', 'LNMIIT Jaipur', 'Jaipur', ['Bengaluru', 'Noida'], ['Python', 'Networking', 'Machine Learning'], 89.7, 7, ['Network Engineering Intern', 'Machine Learning Intern'], 'Telecom'),
  c('C0048', 'Preeti Choudhary', 'OBC', 'B.Sc', 'JECRC University', 'Jaipur', ['Delhi'], ['Communication', 'Excel'], 54.3, 0, ['Digital Marketing Intern'], 'E-Commerce', 2027),

  /* ---- Pune ---- */
  c('C0049', 'Omkar Kulkarni', 'General', 'B.Tech (Mechanical)', 'College of Engineering Pune', 'Pune', ['Mumbai'], ['C++', 'Embedded Systems', 'Networking'], 83.6, 5, ['Embedded Systems Intern'], 'Manufacturing'),
  c('C0050', 'Rutuja Pawar', 'OBC', 'B.Tech (ECE)', 'Vishwakarma Institute of Technology', 'Pune', ['Mumbai', 'Bengaluru'], ['Embedded Systems', 'C++', 'Python'], 79.1, 3, ['Embedded Systems Intern', 'Software Development Intern'], 'Manufacturing'),
  c('C0051', 'Siddharth Rane', 'SC', 'B.Tech (ECE)', 'MIT World Peace University', 'Pune', ['Mumbai'], ['Networking', 'C++', 'Communication'], 71.8, 1, ['Embedded Systems Intern', 'Network Engineering Intern'], 'Manufacturing'),
  c('C0052', 'Alia Merchant', 'General', 'B.Tech (CSE)', 'Pune Institute of Computer Technology', 'Pune', ['Mumbai', 'Bengaluru'], ['Python', 'Web Development', 'SQL'], 76.4, 2, ['Web Development Intern', 'Software Development Intern'], 'Information Technology'),

  /* ---- Additional applicants (later registration window) ---- */
  c('C0053', 'Meghna Rajan', 'OBC', 'B.Des', 'Loyola College', 'Chennai', ['Bengaluru'], ['Web Development', 'Communication', 'Digital Marketing'], 66.0, 1, ['UI/UX Design Intern', 'Digital Marketing Intern'], 'Information Technology'),
  c('C0054', 'Aryan Kapoor', 'General', 'B.Tech (CSE)', 'New Horizon College of Engineering', 'Bengaluru', ['Hyderabad'], ['Java', 'Python', 'SQL', 'Excel'], 82.0, 3, ['Software Development Intern'], 'Information Technology'),
  c('C0055', 'Devika Rathore', 'General', 'BBA', 'Amity University Gurugram', 'Gurugram', ['Delhi'], ['Excel', 'Business Analytics', 'Communication'], 70.8, 2, ['Business Analytics Intern'], 'Consulting'),
  c('C0056', 'Rehan Qureshi', 'OBC', 'B.Tech (IT)', 'Integral University', 'Lucknow', ['Noida'], ['Python', 'Excel', 'SQL'], 71.5, 1, ['Data Science Intern', 'Data Analyst Intern'], 'Public Sector (PSU)'),
  c('C0057', 'Pranav Deshmukh', 'SC', 'B.Tech (ECE)', 'Sinhgad College of Engineering', 'Pune', ['Mumbai'], ['C++', 'Networking', 'Communication'], 69.4, 1, ['Embedded Systems Intern', 'Network Engineering Intern'], 'Manufacturing'),
]

/* ========================================================================== */
/* LOOKUPS + DERIVED HELPERS                                                   */
/* ========================================================================== */

export const candidateById = candidates.reduce((acc, cand) => {
  acc[cand.id] = cand
  return acc
}, {})

export const opportunityById = opportunities.reduce((acc, opp) => {
  acc[opp.id] = opp
  return acc
}, {})

export const TOTAL_SEATS = opportunities.reduce((sum, o) => sum + o.capacity, 0)

/** Skills present in the candidate pool, ranked by frequency. */
export function getSkillFrequency() {
  const counts = {}
  candidates.forEach((cand) => {
    cand.skills.forEach((skill) => {
      counts[skill] = (counts[skill] || 0) + 1
    })
  })
  return Object.entries(counts)
    .map(([skill, count]) => ({ skill, count }))
    .sort((a, b) => b.count - a.count)
}

/** Generic group-and-count helper used by the analytics page. */
export function countBy(items, keyFn) {
  const counts = {}
  items.forEach((item) => {
    const key = keyFn(item)
    if (key === null || key === undefined) return
    counts[key] = (counts[key] || 0) + 1
  })
  return Object.entries(counts)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
}

/** Distinct sorted values of a candidate field, for filter dropdowns. */
export function distinctValues(items, keyFn) {
  return [...new Set(items.map(keyFn).filter(Boolean))].sort()
}

/** Notifications shown in the header bell menu. */
export const notifications = [
  {
    id: 1,
    title: 'Allocation cycle 2026-A open',
    body: '12 internship opportunities published across 10 cities.',
    time: '2 hours ago',
    unread: true,
  },
  {
    id: 2,
    title: 'Reserved seats unfilled',
    body: 'TCS Mumbai (OBC) and Reliance Jio Jaipur (ST) still have vacant reserved seats.',
    time: '5 hours ago',
    unread: true,
  },
  {
    id: 3,
    title: 'Eligibility rules updated',
    body: 'Minimum qualification score for this cycle is set to 55.',
    time: 'Yesterday',
    unread: false,
  },
  {
    id: 4,
    title: 'Demo dataset loaded',
    body: `${candidates.length} candidate profiles imported from the scheme portal.`,
    time: '2 days ago',
    unread: false,
  },
]

/** Copy blocks used on the Methodology page. */
export const METHODOLOGY = {
  problems: [
    'Very large candidate volumes against a small number of internship seats.',
    'Skill mismatch between what candidates offer and what employers require.',
    'Location constraints — candidates cannot always relocate.',
    'Candidate preferences are ignored by first-come-first-served shortlisting.',
    'Reservation and fairness quotas are applied manually and inconsistently.',
    'No audit trail explaining why a particular candidate was or was not selected.',
  ],
  solution: [
    { label: 'Candidate skills', detail: 'Overlap between candidate skills and the skills an internship requires.' },
    { label: 'Educational background', detail: 'Qualification score derived from academics and degree relevance.' },
    { label: 'Preferences', detail: 'Preferred role and sector stated by the candidate at registration.' },
    { label: 'Location', detail: 'Candidate location preference against the posting location.' },
    { label: 'Eligibility', detail: 'Hard rules: minimum score, location match, minimum skill overlap.' },
    { label: 'Reservation policy', detail: 'Reserved-category seats treated as a hard constraint, not a tie-breaker.' },
  ],
  pipeline: [
    { step: 'Candidate Data', detail: 'Profiles, skills, qualification score, category and preferences.' },
    { step: 'Data Preprocessing', detail: 'Normalise skill tags, validate fields, de-duplicate records.' },
    { step: 'Eligibility Filtering', detail: 'Rule-based hard filter removes infeasible candidate–internship pairs.' },
    { step: 'Skill Matching', detail: 'Skill-overlap percentage computed for every surviving pair.' },
    { step: 'Preference Matching', detail: 'Role, sector and location preferences scored.' },
    { step: 'Match Score', detail: 'Weighted fit score (0–100) per candidate–internship pair.' },
    { step: 'Optimization', detail: 'Global assignment maximising total match quality under capacity and quota constraints.' },
    { step: 'Final Allocation', detail: 'One internship per candidate, seats never over-filled, quotas respected.' },
  ],
  benefits: [
    { title: 'Faster allocation', detail: 'A cycle that takes weeks of manual shortlisting resolves in seconds.' },
    { title: 'Better matching', detail: 'Assignments are optimised globally instead of job-by-job.' },
    { title: 'Reduced manual effort', detail: 'Reviewers only handle exceptions, not every application.' },
    { title: 'Transparent scoring', detail: 'Every score is broken down into its contributing components.' },
    { title: 'Fairness by construction', detail: 'Reserved-category seats are enforced as hard constraints.' },
    { title: 'Scalable', detail: 'The same pipeline runs for 50 candidates or 5,00,000.' },
  ],
  engineStack: [
    { layer: 'Eligibility rules', tech: 'Rule-based filter (Python)' },
    { layer: 'Fit scoring', tech: 'Fuzzy logic (scikit-fuzzy)' },
    { layer: 'Acceptance prediction', tech: 'Logistic Regression (scikit-learn)' },
    { layer: 'Optimisation', tech: 'Google OR-Tools CP-SAT (ILP)' },
    { layer: 'Explainability', tech: 'Deterministic evidence layer (FACT / INTERPRETATION / LIMITATION)' },
    { layer: 'This dashboard', tech: 'React + Vite (demo scoring implemented in-browser)' },
  ],
}
