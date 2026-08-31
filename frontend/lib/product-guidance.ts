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
      title: "رتّب مسار بدء مشروعك",
      what: "اجمع قرارات المشروع والمعلومات التي ما زالت تحتاج إلى مراجعة في مكان واحد.",
      why: "تظهر هذه الخطوة لكل نشاط مدعوم كنقطة بداية في الرحلة النموذجية.",
      next: "اكتب قائمة قصيرة بالنقاط غير المحسومة، ثم استخدم مرجع النشاط الرسمي أدناه لمراجعة معلومات النشاط المنشورة.",
    },
    en: {
      title: "Organize your business-start path",
      what: "Bring your project decisions and the information still needing review into one place.",
      why: "This step appears for every supported activity as the starting point of the sample journey.",
      next: "Write down the open decisions, then use the official activity reference below to review the published activity information.",
    },
  },
  demo_employment_setup: {
    ar: {
      title: "رتّب خطة العاملين في المشروع",
      what: "لخّص احتياج المشروع المتوقع من الموظفين أو العمال.",
      why: "ترتبط هذه الخطوة بإجابتك عن وجود موظفين أو عمال في المشروع.",
      next: "سجّل الأدوار والعدد المتوقع، وضع ترتيبات العاملين ضمن الموضوعات التي ستراجعها رسميًا.",
    },
    en: {
      title: "Organize your staffing plan",
      what: "Summarize the staff or workers you expect the business to need.",
      why: "This step is connected to your answer about employing staff or workers.",
      next: "Note the expected roles and headcount, and include staffing arrangements in your official review topics.",
    },
  },
  demo_worker_readiness: {
    ar: {
      title: "جهّز معلومات العاملين داخل المنشأة",
      what: "لخّص من تتوقع أن يعمل داخل منشأة الطعام أو المشروبات.",
      why: "ترتبط هذه الخطوة بإجابتك عن وجود عاملين داخل المنشأة.",
      next: "دوّن الأدوار والعدد المتوقع حتى تكون أسئلتك واضحة عند مراجعة المسار الرسمي المناسب.",
    },
    en: {
      title: "Prepare information about on-site workers",
      what: "Summarize who you expect to work inside the food or beverage establishment.",
      why: "This step is connected to your answer about workers being present inside the establishment.",
      next: "Note the expected roles and headcount so your questions are clear when you review the appropriate official route.",
    },
  },
  demo_delivery_setup: {
    ar: {
      title: "رتّب خطة خدمة التوصيل",
      what: "وضّح كيف تتوقع تقديم خدمة التوصيل ضمن خطة المشروع.",
      why: "ترتبط هذه الخطوة بإجابتك عن تقديم التوصيل المنزلي.",
      next: "دوّن نموذج التوصيل الذي تنوي استخدامه والأسئلة التي تحتاج إلى تأكيد قبل البدء.",
    },
    en: {
      title: "Organize your delivery plan",
      what: "Clarify how you expect delivery to fit into the business plan.",
      why: "This step is connected to your answer about offering home delivery.",
      next: "Note the delivery model you intend to use and the questions you need to confirm before starting.",
    },
  },
  demo_sidewalk_setup: {
    ar: {
      title: "راجع خطة استخدام مساحة الرصيف",
      what: "سجّل الاستخدام الذي تفكر فيه للمساحة العامة أمام المطعم.",
      why: "ترتبط هذه الخطوة بإجابتك عن استخدام الرصيف العام لخدمة العملاء.",
      next: "لا تنفذ الخطة اعتمادًا على هذا المثال؛ احتفظ بالتفاصيل لمراجعتها مع الجهة الرسمية المختصة.",
    },
    en: {
      title: "Review your planned sidewalk use",
      what: "Record how you are considering using the public space outside the restaurant.",
      why: "This step is connected to your answer about using the public sidewalk for customer service.",
      next: "Do not act on the sample item alone; keep the details ready for review with the responsible official authority.",
    },
  },
  demo_vat_confirmation: {
    ar: {
      title: "سجّل نتيجة مراجعة مسار ضريبة القيمة المضافة",
      what: "احتفظ بنتيجة التحقق التي أدخلتها؛ فالدليل لا يحسب حد التسجيل ولا يحدد حالتك الضريبية.",
      why: "ترتبط هذه الخطوة بالحالة التي قلت إنك تحققت منها عبر مسار الهيئة.",
      next: "دوّن نتيجة التحقق وتاريخه حتى تستطيع الرجوع إليهما عند متابعة المشروع.",
    },
    en: {
      title: "Record your VAT-route review outcome",
      what: "Keep the confirmation you entered; the Navigator does not calculate a threshold or determine your tax status.",
      why: "This step is connected to the status you said you had confirmed through the authority's route.",
      next: "Record the outcome and the date you checked it so you can refer back to them during follow-up.",
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
      meaning: "إجابتك عن الشخص أو الجهة التي ستملك المشروع هي نقطة تنظيم هذا الموضوع.",
      importance: "يستخدمها الدليل لترتيب المراجعة فقط، ولا يقرر أهلية الاستثمار أو المسار الذي ينطبق.",
      review: "تأكد من وصف حالة الملكية كما هي، ثم حدّد الوجهة الحكومية الرسمية المناسبة قبل اتخاذ قرار.",
    },
    en: {
      title: "Ownership and investment",
      meaning: "Your answer about the person or entity that will own the business is the starting point for this topic.",
      importance: "The Navigator uses it only to organize review; it does not decide investment eligibility or the route that applies.",
      review: "Confirm that the ownership situation is described accurately, then identify the appropriate official government destination before deciding.",
    },
  },
  business_registration_route: {
    ar: {
      title: "الشكل القانوني والتسجيل",
      meaning: "الشكل الذي تفكر في استخدامه للمشروع، مثل مؤسسة فردية أو شركة ذات مسؤولية محدودة.",
      importance: "يساعد الاختيار على تنظيم موضوع التسجيل، ولا يختار الدليل الشكل الأنسب نيابة عنك.",
      review: "ثبّت اختيارك بعد مراجعة معلومات التسجيل الرسمية أو الحصول على مشورة مختصة.",
    },
    en: {
      title: "Legal form and registration",
      meaning: "The form you are considering for the business, such as an individual establishment or limited liability company.",
      importance: "The answer helps organize the registration topic; the Navigator does not choose the best legal form for you.",
      review: "Confirm your choice after reviewing official registration information or obtaining professional advice.",
    },
  },
  site_activity_verification: {
    ar: {
      title: "اختيار الموقع",
      meaning: "ما إذا كنت اخترت موقعًا للمشروع أم ما زلت تبحث.",
      importance: "يساعد هذا الجواب على ترتيب مراجعة الموقع من دون طلب عنوانك.",
      review: "إذا اخترت موقعًا، قارن خطتك بمعلومات النشاط الرسمية واطلب تأكيدًا رسميًا قبل الاعتماد عليه.",
    },
    en: {
      title: "Choosing premises",
      meaning: "Whether you have selected business premises or are still looking.",
      importance: "This answer helps organize the premises review without asking for your address.",
      review: "If you selected premises, compare your plan with official activity information and seek official confirmation before relying on it.",
    },
  },
  vat_registration_navigation: {
    ar: {
      title: "ضريبة القيمة المضافة",
      meaning: "حالة التحقق التي أدخلتها لمسار التسجيل الإلزامي في ضريبة القيمة المضافة.",
      importance: "يبقي الدليل نتيجة تحققك واضحة، لكنه لا يحسب الإيرادات أو يحدد حالتك الضريبية.",
      review: "إذا لم تكن قد تحققت، استخدم مصدرًا حكوميًا رسميًا محدثًا قبل اعتبار الحالة محسومة.",
    },
    en: {
      title: "Value Added Tax",
      meaning: "The confirmation status you entered for the mandatory VAT-registration route.",
      importance: "The Navigator keeps your confirmation explicit, but it does not calculate revenue or determine your tax status.",
      review: "If you have not confirmed it, use a current official government source before treating the status as settled.",
    },
  },
  e_invoicing_confirmation: {
    ar: {
      title: "الفوترة الإلكترونية",
      meaning: "موضوع لمراجعة التعليمات الحالية للفوترة الإلكترونية في حالتك.",
      importance: "يظهر للتذكير بالمراجعة فقط؛ وظهوره ليس قرارًا بأنها تنطبق على مشروعك.",
      review: "راجع النطاق والتوقيت والخطوات في مصدر حكومي رسمي محدث قبل اتخاذ إجراء.",
    },
    en: {
      title: "E-invoicing",
      meaning: "A topic for reviewing current e-invoicing guidance for your situation.",
      importance: "It appears only as a review reminder; its presence is not a decision that it applies to your business.",
      review: "Review the scope, timing, and steps in a current official government source before acting.",
    },
  },
  zakat_registration_confirmation: {
    ar: {
      title: "الزكاة",
      meaning: "موضوع مستقل لجمع الأسئلة المتعلقة بالزكاة وحالة منشأتك.",
      importance: "يعرضه الدليل للتنقل والمراجعة، ولا يحسب التزامًا أو يقرر نتيجته.",
      review: "راجع حالة منشأتك من خلال مصدر حكومي رسمي محدث قبل اتخاذ إجراء.",
    },
    en: {
      title: "Zakat",
      meaning: "A separate topic for collecting questions about Zakat and your business's situation.",
      importance: "The Navigator shows it for navigation and review; it does not calculate an obligation or decide an outcome.",
      review: "Review your business's situation using a current official government source before acting.",
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
    introTitle: "رتّبنا نتيجتك بناءً على إجاباتك",
    introBody: "ستجد خطوات تبدأ بها، ومعلومات ما زلنا نحتاجها، وموضوعات تراجعها قبل الاعتماد على أي قرار.",
    resultDetermined: "اكتملت الإجابات اللازمة لتحديد الخطوات في هذا السيناريو.",
    progressTitle: "تقدمك في خطوات القائمة",
    applicableItemsTemplate: "عدد الخطوات الظاهرة لهذا المشروع: {total}",
    progressBarLabel: "تقدم إنجاز خطوات القائمة",
    progressDisclaimer: "هذه النسبة تتبع العلامات التي تضعها على خطوات القائمة فقط. ولا تعني امتثالًا أو موافقة أو ترخيصًا أو جاهزية للتشغيل.",
    appliesTitle: "ابدأ بهذه الخطوات",
    appliesBody: "هذه خطوات رتّبها الدليل وفق إجاباتك الحالية.",
    noApplicableItems: "لا توجد خطوة ظاهرة ضمن هذا السيناريو.",
    missingTitle: "نحتاج منك معلومة",
    missingBody: "لا تخمّن. أجب عندما تعرف، أو ارجع إلى السؤال لتعديل اختيارك؛ وستبقى المعلومة غير محسومة حتى ذلك الحين.",
    noMissingInformation: "لا نحتاج إلى إجابة إضافية لتحديد الخطوات الآن.",
    reviewTitle: "راجع هذه الأمور",
    reviewBody: "هذه موضوعات للتوجيه والمراجعة، ولا تدخل في نسبة الإنجاز. وظهورها لا يعني أن الدليل قرر انطباقها تنظيمياً.",
    reviewFallback: "هذا موضوع إرشادي ضمن رحلة المشروع. حدّد ما يحتاجه مشروعك وراجعه من القناة المناسبة قبل اتخاذ قرار.",
    noReviewItems: "لا توجد موضوعات مراجعة إضافية في هذا السيناريو.",
    notSelectedTitle: "خطوات لم تظهر وفق إجاباتك",
    whatLabel: "ما هذه الخطوة؟",
    whyLabel: "لماذا ظهرت؟",
    nextLabel: "ماذا تفعل الآن؟",
    meaningLabel: "ما المقصود؟",
    importanceLabel: "لماذا هذا مهم لمشروعك؟",
    reviewLabel: "ماذا تراجع؟",
    missingReasonTemplate: "نحتاج إجابتك عن «{question}» حتى نعرف إن كانت هذه الخطوة ستظهر في قائمتك.",
    answerNow: "العودة إلى هذا السؤال",
    finalLabel: "ملخص المتابعة",
    finalInProgressTitle: "متابعة خطواتك مستمرة",
    finalNoApplicableTitle: "لا توجد خطوات ظاهرة في هذا السيناريو",
    finalNoApplicableBody: "تعكس هذه النتيجة نطاق العرض التجريبي الحالي وإجاباتك، وليست حكمًا بعدم وجود متطلبات فعلية.",
    finalMissingTitle: "أنجزت الخطوات الظاهرة، وما زلنا نحتاج معلومات",
    finalCompleteTitle: "أنهيت متابعة خطوات القائمة",
    finalCompleteBody: "وضعت علامة إنجاز على جميع الخطوات الظاهرة. هذه متابعة شخصية فقط وليست إثباتًا للامتثال أو الموافقة.",
    finalSummaryTitle: "ما الذي يبقى أمامك؟",
    finalActionsTemplate: "وضعت علامة على {completed} من أصل {total} خطوة.",
    finalMissingTemplate: "إجابات ما زلنا نحتاجها: {count}.",
    finalNoMissing: "لا توجد إجابات ناقصة في النتيجة الحالية.",
    finalReviewTemplate: "موضوعات منفصلة للمراجعة: {count}.",
    finalActivityReference: "مرجع النشاط الرسمي في منصة بلدي ظاهر أعلاه، وهو مستقل عن الخطوات النموذجية.",
  },
  en: {
    introTitle: "We organized your result from your answers",
    introBody: "Below are steps to start, information we still need, and topics to review before relying on a decision.",
    resultDetermined: "The answers needed to select the steps for this scenario are complete.",
    progressTitle: "Your checklist progress",
    applicableItemsTemplate: "Steps shown for this project: {total}",
    progressBarLabel: "Checklist-step completion progress",
    progressDisclaimer: "This percentage tracks only the marks you place on checklist steps. It does not mean compliance, approval, licensing, or readiness to operate.",
    appliesTitle: "Start with these steps",
    appliesBody: "These steps were organized from your current answers.",
    noApplicableItems: "No step is shown in this scenario.",
    missingTitle: "We need information from you",
    missingBody: "Do not guess. Answer when you know, or return to the question to change your choice; the information remains unresolved until then.",
    noMissingInformation: "We do not need another answer to select the steps right now.",
    reviewTitle: "Review these topics",
    reviewBody: "These topics are for navigation and review and do not count toward progress. Their presence is not a regulatory applicability decision.",
    reviewFallback: "This is a guidance topic in the business journey. Identify what your project needs and review it through the appropriate channel before deciding.",
    noReviewItems: "There are no additional review topics in this scenario.",
    notSelectedTitle: "Steps not shown for your answers",
    whatLabel: "What is this step?",
    whyLabel: "Why did it appear?",
    nextLabel: "What should you do now?",
    meaningLabel: "What does this mean?",
    importanceLabel: "Why does this matter for your project?",
    reviewLabel: "What should you review?",
    missingReasonTemplate: "We need your answer to “{question}” to know whether this step should appear in your checklist.",
    answerNow: "Return to this question",
    finalLabel: "Follow-up summary",
    finalInProgressTitle: "Your checklist follow-up is in progress",
    finalNoApplicableTitle: "No steps are shown in this scenario",
    finalNoApplicableBody: "This reflects the current demo scope and your answers; it is not a decision that no real requirements exist.",
    finalMissingTitle: "You marked the shown steps, but information is still missing",
    finalCompleteTitle: "You finished following up on the checklist steps",
    finalCompleteBody: "You marked every shown step complete. This is personal tracking only, not evidence of compliance or approval.",
    finalSummaryTitle: "What remains in your journey?",
    finalActionsTemplate: "You marked {completed} of {total} steps.",
    finalMissingTemplate: "Answers still needed: {count}.",
    finalNoMissing: "There are no missing answers in the current result.",
    finalReviewTemplate: "Separate topics to review: {count}.",
    finalActivityReference: "The official Balady activity reference appears above and is separate from the synthetic checklist steps.",
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
