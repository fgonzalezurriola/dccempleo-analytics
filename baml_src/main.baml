enum Seniority {
  INTERN
  TRAINEE
  JUNIOR
  MID_SENIOR
  SENIOR
  MIXED
  UNKNOWN
}

enum OfferType {
  JOB
  PRACTICE
  BOOTCAMP
  COURSE
  UNKNOWN
}

class OfferAnalysis {
  seniority Seniority
  offer_type OfferType
  tech_stack string[] @description("Lowercased canonical technologies.")
  confidence float @description("A confidence score between 0 and 1.")
  signals string[] @description("Short evidence snippets found in the offer text.")
}

function ExtractOffer(text: string) -> OfferAnalysis {
  client OpenCodeBridge
  prompt #"
    You classify Telegram tech-job posts from Chile.
    Return structured output only.
    IMPORTANT: Output ONLY these keys: seniority, offer_type, tech_stack, confidence, signals.
    Do NOT include any additional keys.

    SENIORITY RULES:
    - INTERN or TRAINEE: internship/practice/student roles
      Keywords: practica, práctica, practicante, trainee, internship, intern, estudiante.
    - JUNIOR: explicitly junior/entry-level or 0-2 years.
    - MID_SENIOR: semi senior, semi-senior, ssr, middle, mid-level, or mixed "semi senior / senior".
    - SENIOR: explicitly senior/sr/lead/staff/principal.
    - MIXED: if truly incompatible seniority levels are explicitly required.
    - UNKNOWN: no reliable signal.

    OFFER TYPE:
    - PRACTICE for internships/practica/practicante.
    - BOOTCAMP for bootcamp.
    - COURSE for courses/certification/training.
    - JOB for regular hiring.
    - UNKNOWN if unclear.

    TECH STACK NORMALIZATION:
    - Use lowercase canonical names.
    - go and golang => go
    - csharp and c# => c#
    - node, nodejs, node.js => node.js
    - postgres => postgresql
    - amazon web services => aws
    - google cloud => gcp
    - If typescript and javascript are both mentioned as the same stack, keep only typescript.
      Keep both only if they are explicitly distinct requirements.

    Text:
    {{ text }}
  "#
}
