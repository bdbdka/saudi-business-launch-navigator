import type { Locale } from "@/lib/i18n";

export type RequirementProductGuidance = Readonly<{
  title: string;
  what: string;
  why: string;
  next: string;
}>;

export type ReviewTopicProductGuidance = Readonly<{
  title: string;
  meaning: string;
  importance: string;
  review: string;
}>;

export type MissingNavigationProductGuidance = Readonly<{
  title: string;
  body: string;
}>;

export type ResultProductCopy = Readonly<{
  introTitle: string;
  introBody: string;
  resultDetermined: string;
  progressTitle: string;
  applicableItemsTemplate: string;
  progressBarLabel: string;
  progressDisclaimer: string;
  appliesTitle: string;
  appliesBody: string;
  noApplicableItems: string;
  missingTitle: string;
  missingBody: string;
  noMissingInformation: string;
  reviewTitle: string;
  reviewBody: string;
  reviewFallback: string;
  noReviewItems: string;
  notSelectedTitle: string;
  whatLabel: string;
  whyLabel: string;
  nextLabel: string;
  meaningLabel: string;
  importanceLabel: string;
  reviewLabel: string;
  missingReasonTemplate: string;
  answerNow: string;
  finalLabel: string;
  finalInProgressTitle: string;
  finalNoApplicableTitle: string;
  finalNoApplicableBody: string;
  finalMissingTitle: string;
  finalCompleteTitle: string;
  finalCompleteBody: string;
  finalSummaryTitle: string;
  finalActionsTemplate: string;
  finalMissingTemplate: string;
  finalNoMissing: string;
  finalReviewTemplate: string;
  finalActivityReference: string;
}>;

const requirementCodes = [
  "demo_launch_orientation",
  "demo_employment_setup",
  "demo_worker_readiness",
  "demo_delivery_setup",
  "demo_sidewalk_setup",
  "demo_vat_confirmation",
] as const;

type DemoRequirementCode = (typeof requirementCodes)[number];

const requirementGuidance: Record<
  DemoRequirementCode,
  Record<Locale, RequirementProductGuidance>
> = {
  demo_launch_orientation: {
    ar: {
      title: "رتّب قرارات مشروعك الأساسية",
      what: "اجمع القرارات والمعلومات التي لم تحسمها بعد حتى تعرف ما يحتاج إلى مراجعة قبل أن تنتقل للخطوات التالية.",
      why: "يساعدك ذلك على تمييز ما أصبح واضحًا عن النقاط التي ما زالت تحتاج إلى قرار أو تحقق.",
      next: "دوّن النقاط غير المحسومة، مثل شكل المنشأة أو الموقع أو الموظفين أو طريقة التشغيل، ثم راجع كل نقطة من مصدرها الرسمي عند الحاجة.",
    },
    en: {
      title: "Organize your key business decisions",
      what: "Bring together the decisions and information you have not settled so you know what needs review before moving forward.",
      why: "This helps you separate what is already clear from points that still need a decision or verification.",
      next: "List open points such as legal form, premises, staffing, or operating model, then check each one through an official source when needed.",
    },
  },
  demo_employment_setup: {
    ar: {
      title: "رتّب خطة العاملين في المشروع",
      what: "حدّد الوظائف التي سيحتاجها مشروعك وعدد الأشخاص المتوقع في البداية.",
      why: "تساعدك الخطة المبكرة على تنظيم احتياج المشروع وتقدير مسؤوليات التشغيل بوضوح.",
      next: "سجّل الأدوار والعدد المتوقع، ثم ضع ترتيبات العاملين ضمن الموضوعات التي ستراجعها رسميًا.",
    },
    en: {
      title: "Organize your staffing plan",
      what: "Identify the roles your business will need and the number of people you expect at the start.",
      why: "An early plan helps you organize staffing needs and clarify operating responsibilities.",
      next: "Record the expected roles and headcount, then include staffing arrangements in the topics you review officially.",
    },
  },
  demo_worker_readiness: {
    ar: {
      title: "جهّز معلومات العاملين داخل المنشأة",
      what: "حدّد من سيعمل داخل موقع إعداد الطعام أو المشروبات وما الأدوار التي سيتولاها.",
      why: "معرفة فريق الموقع تساعدك على ترتيب مسؤوليات العمل اليومية والأسئلة التي تحتاج إلى مراجعة.",
      next: "دوّن الأدوار والعدد المتوقع داخل الموقع حتى تكون مراجعتك للمسار الرسمي أكثر وضوحًا.",
    },
    en: {
      title: "Prepare information about on-site workers",
      what: "Identify who will work at the food or beverage premises and the roles they will perform.",
      why: "Knowing the on-site team helps you organize daily responsibilities and the questions that need review.",
      next: "Record the expected on-site roles and headcount so your review of the official route is clearer.",
    },
  },
  demo_delivery_setup: {
    ar: {
      title: "رتّب خطة خدمة التوصيل",
      what: "حدّد كيف ستصل الطلبات إلى العملاء، سواء بالتوصيل المباشر أو عبر منصة خارجية.",
      why: "اختيار طريقة التوصيل مبكرًا يساعدك على تنظيم التشغيل والتكاليف والمسؤوليات.",
      next: "دوّن طريقة التوصيل التي تنوي استخدامها والأسئلة التي تحتاج إلى تأكيد قبل البدء.",
    },
    en: {
      title: "Organize your delivery plan",
      what: "Decide how orders will reach customers, whether through direct delivery or a third-party platform.",
      why: "Choosing the delivery approach early helps you organize operations, costs, and responsibilities.",
      next: "Record the delivery approach you plan to use and the questions you need to confirm before starting.",
    },
  },
  demo_sidewalk_setup: {
    ar: {
      title: "راجع خطة استخدام مساحة الرصيف",
      what: "وضّح كيف تفكر في استخدام المساحة العامة أمام المطعم لخدمة العملاء.",
      why: "استخدام مساحة عامة يحتاج إلى تحقق منفصل قبل أن تعتمد عليه في تصميم الموقع أو تشغيله.",
      next: "احتفظ بتفاصيل المساحة والاستخدام المقترح، وراجعها مع الجهة الرسمية المختصة قبل التنفيذ.",
    },
    en: {
      title: "Review your planned sidewalk use",
      what: "Clarify how you are considering using public space outside the restaurant for customer service.",
      why: "Using public space needs separate confirmation before it becomes part of the premises design or operation.",
      next: "Keep the proposed space and use details ready, and review them with the responsible official authority before acting.",
    },
  },
  demo_vat_confirmation: {
    ar: {
      title: "سجّل نتيجة مراجعة مسار ضريبة القيمة المضافة",
      what: "احتفظ بنتيجة التحقق التي حصلت عليها، وسجّل المعلومات التي اعتمدت عليها عند المراجعة.",
      why: "تسجيل النتيجة وتاريخها يمنع ضياع ما تحققت منه ويسهّل عليك متابعته لاحقًا.",
      next: "دوّن نتيجة التحقق وتاريخه، وارجع إلى مسار الهيئة إذا تغيرت معلومات مشروعك.",
    },
    en: {
      title: "Record your VAT-route review outcome",
      what: "Keep the confirmation you obtained and record the information you relied on during the review.",
      why: "Recording the outcome and date helps preserve what you verified and makes later follow-up easier.",
      next: "Record the outcome and date, and return to the authority's route if your business information changes.",
    },
  },
};

const reviewTopicCodes = [
  "ownership_investment_route",
  "business_registration_route",
  "site_activity_verification",
  "vat_registration_navigation",
  "e_invoicing_confirmation",
  "zakat_registration_confirmation",
] as const;

type DemoReviewTopicCode = (typeof reviewTopicCodes)[number];

const reviewTopicGuidance: Record<
  DemoReviewTopicCode,
  Record<Locale, ReviewTopicProductGuidance>
> = {
  ownership_investment_route: {
    ar: {
      title: "الملكية والاستثمار",
      meaning: "حدّد الشخص أو الجهة التي ستملك المنشأة قانونيًا، وليس فقط من سيديرها يوميًا.",
      importance: "نوع الملكية قد يؤثر في المسار الذي تحتاج إلى مراجعته قبل تأسيس المنشأة.",
      review: "تأكد من وصف حالة الملكية بدقة، ثم راجع الجهة الحكومية المناسبة قبل اتخاذ قرار استثماري.",
    },
    en: {
      title: "Ownership and investment",
      meaning: "Identify the person or entity that will legally own the business, not only who will manage it day to day.",
      importance: "The ownership type may affect the route you need to review before establishing the business.",
      review: "Describe the ownership situation accurately, then review the appropriate government route before making an investment decision.",
    },
  },
  business_registration_route: {
    ar: {
      title: "الشكل القانوني والتسجيل",
      meaning: "الصيغة التي ستسجل بها المنشأة، مثل مؤسسة فردية أو شركة ذات مسؤولية محدودة.",
      importance: "اختيار الشكل القانوني يؤثر في طريقة التسجيل والمسؤوليات المرتبطة بالمنشأة.",
      review: "قارن الخيارات المتاحة، ثم ثبّت اختيارك بعد مراجعة معلومات التسجيل الرسمية أو الحصول على مشورة مختصة.",
    },
    en: {
      title: "Legal form and registration",
      meaning: "The structure used to register the business, such as an individual establishment or limited liability company.",
      importance: "The legal form affects the registration route and the responsibilities connected to the business.",
      review: "Compare the available options, then confirm your choice after reviewing official registration information or obtaining professional advice.",
    },
  },
  site_activity_verification: {
    ar: {
      title: "اختيار الموقع",
      meaning: "تحقق من أن الموقع الذي تفكر فيه مناسب لنوع النشاط وطريقة التشغيل المخططة.",
      importance: "اختيار الموقع مبكرًا من دون تحقق قد يسبب تغيير الخطة أو تكاليف إضافية لاحقًا.",
      review: "قارن الموقع بمعلومات النشاط الرسمية، واطلب تأكيدًا من الجهة المختصة قبل الاعتماد عليه.",
    },
    en: {
      title: "Choosing premises",
      meaning: "Check whether the premises you are considering suit the activity and your planned operating model.",
      importance: "Committing to premises before verification can lead to plan changes or added costs later.",
      review: "Compare the premises with official activity information and seek confirmation from the responsible authority before relying on it.",
    },
  },
  vat_registration_navigation: {
    ar: {
      title: "ضريبة القيمة المضافة",
      meaning: "راجع ما إذا كان التسجيل في ضريبة القيمة المضافة مطلوبًا لحالة منشأتك.",
      importance: "قد تتغير نتيجة المراجعة عندما تتغير معلومات مشروعك، لذلك من المهم التحقق وفق بياناتك الحالية.",
      review: "استخدم مسارًا حكوميًا رسميًا محدثًا، واحتفظ بنتيجة التحقق وتاريخه.",
    },
    en: {
      title: "Value Added Tax",
      meaning: "Review whether VAT registration is required for your business situation.",
      importance: "The review outcome may change when your business information changes, so it matters to check against your current details.",
      review: "Use a current official government route and retain the outcome and date of your check.",
    },
  },
  e_invoicing_confirmation: {
    ar: {
      title: "الفوترة الإلكترونية",
      meaning: "راجع متطلبات الفوترة الإلكترونية التي قد ترتبط بطريقة إصدار منشأتك للفواتير.",
      importance: "معرفة النطاق والتوقيت مبكرًا تساعدك على اختيار طريقة إصدار الفواتير والاستعداد لها.",
      review: "تحقق من النطاق والتوقيت والخطوات عبر مصدر حكومي رسمي محدث قبل اتخاذ إجراء.",
    },
    en: {
      title: "E-invoicing",
      meaning: "Review the e-invoicing requirements that may relate to how your business issues invoices.",
      importance: "Understanding the scope and timing early helps you choose and prepare your invoicing approach.",
      review: "Check the scope, timing, and steps through a current official government source before acting.",
    },
  },
  zakat_registration_confirmation: {
    ar: {
      title: "الزكاة",
      meaning: "راجع ما يرتبط بالزكاة وفق شكل المنشأة وملكيتها ووضعها الفعلي.",
      importance: "التحقق المبكر يوضح ما الذي يحتاج إلى متابعة قبل أن تعتمد خطة التسجيل أو التشغيل.",
      review: "تحقق من حالة منشأتك عبر مصدر حكومي رسمي محدث قبل اتخاذ إجراء.",
    },
    en: {
      title: "Zakat",
      meaning: "Review the Zakat topic in light of the business's legal form, ownership, and actual situation.",
      importance: "Early verification clarifies what needs follow-up before you rely on a registration or operating plan.",
      review: "Check your business's situation through a current official government source before acting.",
    },
  },
};

const missingNavigationGuidance: Record<string, Record<Locale, MissingNavigationProductGuidance>> = {
  ownership_investor_route: {
    ar: {
      title: "لم تحدد حالة الملكية بعد",
      body: "اختر الحالة الأقرب أو «لست متأكدًا» حتى نرتب موضوع الملكية والاستثمار من دون افتراض.",
    },
    en: {
      title: "You have not selected an ownership situation yet",
      body: "Choose the closest option or “Not sure” so we can organize the ownership topic without making an assumption.",
    },
  },
  planned_legal_form: {
    ar: {
      title: "لم تحدد الشكل القانوني بعد",
      body: "اختر الشكل الذي تفكر فيه أو «لم أحدد بعد» حتى نرتب موضوع التسجيل من دون اختيار نيابة عنك.",
    },
    en: {
      title: "You have not selected a legal form yet",
      body: "Choose the form you are considering or “Not decided yet” so we can organize the registration topic without choosing for you.",
    },
  },
  has_selected_business_premises: {
    ar: {
      title: "لم تحدد حالة موقع المشروع بعد",
      body: "أخبرنا هل اخترت موقعًا أو اختر «لست متأكدًا» حتى نرتب موضوع الموقع من دون طلب عنوان.",
    },
    en: {
      title: "You have not provided the premises status yet",
      body: "Tell us whether premises have been selected, or choose “Not sure,” so we can organize the topic without asking for an address.",
    },
  },
};

const resultCopy: Record<Locale, ResultProductCopy> = {
  ar: {
    introTitle: "رتّبنا لك الخطوات بناءً على إجاباتك",
    introBody: "ابدأ بما يناسب حالتك، وراجع النقاط التي ما زالت تحتاج إلى معلومة أو تحقق.",
    resultDetermined: "اكتملت المعلومات اللازمة لعرض خطواتك الحالية.",
    progressTitle: "تقدمك في خطوات القائمة",
    applicableItemsTemplate: "لديك {total} خطوات في القائمة",
    progressBarLabel: "تقدم إنجاز خطوات القائمة",
    progressDisclaimer: "تقيس هذه النسبة ما علّمته كمنجز فقط، ولا تعني امتثالًا أو ترخيصًا أو جاهزية للتشغيل.",
    appliesTitle: "ابدأ بهذه الخطوات",
    appliesBody: "ظهرت هذه الخطوات بناءً على إجاباتك الحالية.",
    noApplicableItems: "لا توجد خطوات ظاهرة بناءً على إجاباتك الحالية.",
    missingTitle: "نحتاج منك معلومة",
    missingBody: "نحتاج هذه المعلومة حتى نحدد النتيجة بشكل أدق. يمكنك العودة إلى السؤال متى عرفت الإجابة.",
    noMissingInformation: "لا نحتاج إلى إجابة إضافية لتحديد الخطوات الآن.",
    reviewTitle: "راجع هذه الأمور",
    reviewBody: "هذه موضوعات مهمة لمتابعة مشروعك، لكنها لا تدخل في نسبة الإنجاز وقد تحتاج إلى مراجعة رسمية منفصلة.",
    reviewFallback: "حدّد ما يحتاجه مشروعك في هذا الموضوع، وراجعه عبر القناة المناسبة قبل اتخاذ قرار.",
    noReviewItems: "لا توجد موضوعات إضافية للمراجعة الآن.",
    notSelectedTitle: "خطوات لم تظهر وفق إجاباتك",
    whatLabel: "المقصود",
    whyLabel: "لماذا تهمك",
    nextLabel: "خطوتك التالية",
    meaningLabel: "المقصود",
    importanceLabel: "لماذا يهمك",
    reviewLabel: "ما الذي تراجعه",
    missingReasonTemplate: "لم نتمكن من تحديد هذه الخطوة لأن إجابتك عن «{question}» ما زالت غير محسومة.",
    answerNow: "العودة إلى هذا السؤال",
    finalLabel: "ملخص المتابعة",
    finalInProgressTitle: "ما زالت لديك خطوات لم تحددها كمنجزة",
    finalNoApplicableTitle: "لا توجد خطوات ظاهرة بناءً على إجاباتك الحالية",
    finalNoApplicableBody: "راجع إجاباتك وموضوعات المراجعة ومرجع النشاط الرسمي قبل اتخاذ قرار.",
    finalMissingTitle: "أنجزت الخطوات الظاهرة، وما زلنا نحتاج معلومات",
    finalCompleteTitle: "حددت جميع خطوات القائمة كمنجزة",
    finalCompleteBody: "اكتمل تتبع الخطوات التي وضعت عليها علامة إنجاز. تابع موضوعات المراجعة ومرجع النشاط الرسمي عند الحاجة.",
    finalSummaryTitle: "ملخص ما تبقى أمامك",
    finalActionsTemplate: "وضعت علامة إنجاز على {completed} من أصل {total} خطوة.",
    finalMissingTemplate: "إجابات ما زلنا نحتاجها: {count}.",
    finalNoMissing: "لا توجد إجابات ناقصة في النتيجة الحالية.",
    finalReviewTemplate: "موضوعات منفصلة للمراجعة: {count}.",
    finalActivityReference: "يمكنك الرجوع إلى مرجع النشاط الرسمي في منصة بلدي أعلاه.",
  },
  en: {
    introTitle: "We organized your result from your answers",
    introBody: "Below are steps to start, information we still need, and topics to review before relying on a decision.",
    resultDetermined: "We have the information needed to show your current steps.",
    progressTitle: "Your checklist progress",
    applicableItemsTemplate: "You have {total} steps in your checklist",
    progressBarLabel: "Checklist-step completion progress",
    progressDisclaimer: "This percentage tracks only the marks you place on checklist steps. It does not mean compliance, approval, licensing, or readiness to operate.",
    appliesTitle: "Start with these steps",
    appliesBody: "These steps were organized from your current answers.",
    noApplicableItems: "No steps are shown for your current answers.",
    missingTitle: "We need information from you",
    missingBody: "Do not guess. Answer when you know, or return to the question to change your choice; the information remains unresolved until then.",
    noMissingInformation: "We do not need another answer to select the steps right now.",
    reviewTitle: "Review these topics",
    reviewBody: "These topics matter to your project, but they are outside completion progress and may need separate official review.",
    reviewFallback: "Identify what your project needs in this area and review it through the appropriate channel before deciding.",
    noReviewItems: "There are no additional review topics right now.",
    notSelectedTitle: "Steps not shown for your answers",
    whatLabel: "What it means",
    whyLabel: "Why it matters",
    nextLabel: "Your next step",
    meaningLabel: "What it means",
    importanceLabel: "Why it matters",
    reviewLabel: "What to review",
    missingReasonTemplate: "We need your answer to “{question}” to know whether this step should appear in your checklist.",
    answerNow: "Return to this question",
    finalLabel: "Follow-up summary",
    finalInProgressTitle: "Your checklist follow-up is in progress",
    finalNoApplicableTitle: "No steps are shown for your current answers",
    finalNoApplicableBody: "Review your answers, the separate review topics, and the official activity reference before deciding.",
    finalMissingTitle: "You marked the shown steps, but information is still missing",
    finalCompleteTitle: "You finished following up on the checklist steps",
    finalCompleteBody: "You finished tracking the steps you marked complete. Follow up on the review topics and official activity reference when needed.",
    finalSummaryTitle: "What remains in your journey?",
    finalActionsTemplate: "You marked {completed} of {total} steps.",
    finalMissingTemplate: "Answers still needed: {count}.",
    finalNoMissing: "There are no missing answers in the current result.",
    finalReviewTemplate: "Separate topics to review: {count}.",
    finalActivityReference: "You can return to the official Balady activity reference above.",
  },
};

export function requirementProductGuidance(
  code: string,
  locale: Locale,
): RequirementProductGuidance | null {
  if (!isDemoRequirementCode(code)) return null;
  return requirementGuidance[code][locale];
}

export function reviewTopicProductGuidance(
  code: string,
  locale: Locale,
): ReviewTopicProductGuidance | null {
  if (!isDemoReviewTopicCode(code)) return null;
  return reviewTopicGuidance[code][locale];
}

export function missingNavigationProductGuidance(
  code: string,
  locale: Locale,
): MissingNavigationProductGuidance | null {
  return missingNavigationGuidance[code]?.[locale] ?? null;
}

export function resultProductCopy(locale: Locale): ResultProductCopy {
  return resultCopy[locale];
}

export function demoRequirementOrder(code: string): number {
  const index = requirementCodes.indexOf(code as DemoRequirementCode);
  return index >= 0 ? index : requirementCodes.length;
}

export function demoReviewTopicOrder(code: string): number {
  const index = reviewTopicCodes.indexOf(code as DemoReviewTopicCode);
  return index >= 0 ? index : reviewTopicCodes.length;
}

function isDemoRequirementCode(code: string): code is DemoRequirementCode {
  return requirementCodes.includes(code as DemoRequirementCode);
}

function isDemoReviewTopicCode(code: string): code is DemoReviewTopicCode {
  return reviewTopicCodes.includes(code as DemoReviewTopicCode);
}
