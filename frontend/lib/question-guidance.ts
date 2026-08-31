import type { QuestionFactCode } from "@/lib/api/types";
import type { Locale } from "@/lib/i18n";

type Guidance = {
  prompt?: string;
  meaning: string;
  why: string;
  example?: string;
};

type LocalizedGuidance = Record<Locale, Guidance>;

const questionGuidance: Record<QuestionFactCode, LocalizedGuidance> = {
  ownership_investor_route: {
    ar: {
      meaning: "المقصود مالك المشروع أو الجهة التي ستملك المنشأة قانونيًا، وليس الشخص الذي سيدير العمل يوميًا.",
      why: "نوع الملكية يغيّر مسار الملكية والاستثمار الذي تحتاج إلى مراجعته.",
      example: "إذا كنت ستملك المشروع بصفتك فردًا سعوديًا، اختر خيار الفرد السعودي حتى لو عيّنت مديرًا آخر.",
    },
    en: {
      meaning: "This means the person or entity that will legally own the business, not the person managing daily operations.",
      why: "The ownership type changes which ownership and investment route you should review.",
      example: "If you will own the business as a Saudi individual, choose that option even if someone else will manage it.",
    },
  },
  planned_legal_form: {
    ar: {
      meaning: "الشكل القانوني هو الصيغة التي تنوي تسجيل المنشأة بها، مثل مؤسسة فردية أو شركة ذات مسؤولية محدودة. وهو مختلف عن نوع النشاط.",
      why: "إجابتك تساعد الدليل على توجيهك إلى موضوع التسجيل المناسب من دون افتراض اختيار نيابةً عنك.",
      example: "«مطعم» هو النشاط، أما «شركة ذات مسؤولية محدودة» فهي شكل قانوني محتمل لتسجيله.",
    },
    en: {
      meaning: "The legal form is how you plan to register the business, such as an individual establishment or limited liability company. It is different from the activity.",
      why: "Your answer helps the guide point you to the relevant registration topic without choosing a structure for you.",
      example: "“Restaurant” is the activity; “limited liability company” is one possible legal form for registering it.",
    },
  },
  has_selected_business_premises: {
    ar: {
      prompt: "هل اخترت موقعًا محددًا أو وضعت موقعًا ضمن خياراتك الجدية؟",
      meaning: "اختر «نعم» إذا حددت موقعًا أو وضعت موقعًا معينًا ضمن خياراتك الجدية. لا نطلب منك إدخال العنوان.",
      why: "معرفة حالة الموقع تحدد ما إذا كان من المفيد إظهار توجيه لمراجعة ملاءمة الموقع للنشاط.",
      example: "إذا كنت تقارن عدة أحياء فقط ولم تحدد عقارًا بعينه، فاختر «لا». وإذا عاينت عقارًا محددًا بجدية، فاختر «نعم».",
    },
    en: {
      prompt: "Have you selected or seriously shortlisted specific premises?",
      meaning: "Choose “Yes” if you have selected or seriously shortlisted specific premises. We do not ask for the address.",
      why: "Knowing the premises status determines whether site-suitability review guidance is useful now.",
      example: "Choose “No” if you are only comparing neighbourhoods; choose “Yes” if a particular site is under serious consideration.",
    },
  },
  has_employees: {
    ar: {
      meaning: "المقصود أشخاص ستوظفهم المنشأة للعمل لديها. لا يشمل ذلك سائقي منصات التوصيل أو المقاولين الخارجيين الذين لا توظفهم المنشأة.",
      why: "وجود موظفين يغيّر الخطوات النموذجية المتعلقة بتجهيز مسار التوظيف.",
      example: "عامل المطبخ الذي توظفه المنشأة يُعد موظفًا، أما سائق تطبيق توصيل مستقل فلا يُعد موظفًا لديها.",
    },
    en: {
      meaning: "This means people the business will employ. It does not include third-party delivery drivers or external contractors who are not employed by the business.",
      why: "Having employees changes the sample steps shown for employment setup.",
      example: "A kitchen worker employed by the business counts; an independent delivery-platform driver does not.",
    },
  },
  gosi_coverage_conditions_met: {
    ar: {
      prompt: "هل تحققت رسميًا من انطباق شروط التأمينات الاجتماعية على منشأتك؟",
      meaning: "السؤال لا يطلب منك تقدير الحالة. أجب فقط إذا تحققت من شروط الخضوع الرسمية للتأمينات الاجتماعية لحالة منشأتك.",
      why: "الإجابة تحدد ما إذا كان مسار المتابعة المتعلق بالتأمينات سيظهر ضمن خطوات النسخة التجريبية.",
      example: "إذا لم تراجع الشروط الرسمية بعد، اختر «لست متأكدًا» بدل التخمين.",
    },
    en: {
      prompt: "Have you officially confirmed whether GOSI coverage conditions apply to your business?",
      meaning: "This question does not ask you to estimate. Answer only if the official GOSI coverage conditions have been checked for your business situation.",
      why: "The answer determines whether the demo's GOSI follow-up path appears in your steps.",
      example: "If you have not reviewed the official conditions yet, choose “Not sure” rather than guessing.",
    },
  },
  has_food_establishment_workers: {
    ar: {
      meaning: "المقصود الأشخاص الذين سيعملون داخل منشأة الطعام أو المشروبات نفسها. هذا أضيق من السؤال السابق الذي يشمل جميع موظفي المشروع.",
      why: "وجود عاملين داخل المنشأة يغيّر خطوة الاستعداد التشغيلي النموذجية التي يعرضها الدليل.",
      example: "المحاسب الذي يعمل عن بُعد قد يكون موظفًا، لكنه لا يعمل داخل منشأة الطعام؛ أما الطاهي أو مقدم المشروبات فيعمل داخلها.",
    },
    en: {
      meaning: "This means people who will work inside the food or beverage premises. It is narrower than the previous question about all business employees.",
      why: "On-site food-establishment workers change the sample operational-readiness step shown by the guide.",
      example: "A remote accountant may be an employee but does not work inside the food premises; a cook or drink preparer does.",
    },
  },
  zatca_confirmed_mandatory_vat_registration_applies: {
    ar: {
      prompt: "هل أكدت عبر هيئة الزكاة والضريبة والجمارك أن التسجيل الإلزامي في ضريبة القيمة المضافة ينطبق على منشأتك؟",
      meaning: "نسألك هل تحققت بالفعل من حالة التسجيل الإلزامي لضريبة القيمة المضافة عبر هيئة الزكاة والضريبة والجمارك. الدليل لا يحسب الإيرادات أو يحدد حالتك الضريبية.",
      why: "لا تظهر خطوة ضريبة القيمة المضافة النموذجية إلا بحسب الحالة التي أكدتَها رسميًا؛ وعدم التأكد يبقى معلومة ناقصة.",
      example: "إذا لم تتحقق عبر الهيئة، اختر «لم أتأكد عبر الهيئة بعد» حتى لو كنت تتوقع أن التسجيل مطلوب.",
    },
    en: {
      prompt: "Have you confirmed through ZATCA whether mandatory VAT registration applies to your business?",
      meaning: "We are asking whether you already confirmed mandatory VAT registration status through the Zakat, Tax and Customs Authority (ZATCA). The guide does not calculate revenue or decide your tax status.",
      why: "The sample VAT step follows only the status you officially confirmed; an unconfirmed status remains missing information.",
      example: "If you have not checked through ZATCA, choose “I have not confirmed through ZATCA yet” even if you expect registration may be required.",
    },
  },
  offers_home_delivery: {
    ar: {
      prompt: "هل ستتيح المنشأة توصيل الطلبات إلى العملاء؟",
      meaning: "اختر «نعم» إذا كنت تخطط لإتاحة توصيل طلبات المنشأة إلى العملاء، سواء نفذته المنشأة مباشرة أو عبر منصة توصيل خارجية.",
      why: "خيار التوصيل يغيّر خطوة الاستعداد للتوصيل التي تظهر في القائمة النموذجية.",
      example: "إذا كانت الطلبات ستُستلم من الموقع فقط ولا يوجد توصيل، اختر «لا».",
    },
    en: {
      prompt: "Will customers be able to receive the business's orders by delivery?",
      meaning: "Choose “Yes” if customers will be able to receive the business's orders by delivery, whether fulfilled directly or through a third-party platform.",
      why: "Offering delivery changes the sample delivery-readiness step shown in the checklist.",
      example: "Choose “No” if orders will only be collected from the premises and delivery is not offered.",
    },
  },
  uses_public_sidewalk_for_customer_service: {
    ar: {
      meaning: "المقصود استخدام جزء من الرصيف العام خارج حدود موقع المنشأة لخدمة العملاء، وليس مساحة خاصة داخل الموقع.",
      why: "استخدام مساحة عامة يغيّر موضوع المراجعة الذي يظهر لك قبل التخطيط للخدمة الخارجية.",
      example: "وضع طاولات لخدمة العملاء على الرصيف العام يُعد استخدامًا؛ أما الطاولات داخل حدود الموقع الخاص فلا يشملها هذا السؤال.",
    },
    en: {
      prompt: "Will the restaurant use the public sidewalk in front of the premises to serve customers?",
      meaning: "This means using part of the public sidewalk outside the business premises to serve customers, not private space within the premises.",
      why: "Using public space changes the review topic shown before planning outdoor customer service.",
      example: "Customer tables on a public sidewalk count; tables fully inside the private premises do not.",
    },
  },
};

export function getQuestionGuidance(code: QuestionFactCode, locale: Locale): Guidance {
  return questionGuidance[code][locale];
}
