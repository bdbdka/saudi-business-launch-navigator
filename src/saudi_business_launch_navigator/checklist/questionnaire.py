"""Bilingual questions for governed, decision-changing facts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthoredOption:
    value: str
    label_ar: str
    label_en: str


@dataclass(frozen=True)
class AuthoredQuestion:
    """Interface copy only; never an official quotation or legal condition."""

    question_ar: str
    question_en: str
    help_text_ar: str
    help_text_en: str
    true_label_ar: str = "نعم"
    true_label_en: str = "Yes"
    false_label_ar: str = "لا"
    false_label_en: str = "No"
    unknown_label_ar: str = "لست متأكدًا"
    unknown_label_en: str = "Not sure"
    options: tuple[AuthoredOption, ...] = ()


QUESTION_TEXT: dict[str, AuthoredQuestion] = {
    "ownership_investor_route": AuthoredQuestion(
        question_ar="من سيملك المشروع؟",
        question_en="Who will own the business?",
        help_text_ar=(
            "اختر الخيار الأقرب لحالتك. إذا لم تكن متأكدًا، اختر «لست متأكدًا» وسنوجهك للجهة الرسمية."
        ),
        help_text_en=(
            "Choose the option closest to your situation. If you are unsure, choose "
            "“Not sure” and we will direct you to the official authority."
        ),
        options=(
            AuthoredOption(
                value="saudi_person_or_saudi_owned_entity",
                label_ar="فرد سعودي أو منشأة مملوكة سعودياً",
                label_en="Saudi person or Saudi-owned entity",
            ),
            AuthoredOption(
                value="gcc_person_or_wholly_gcc_owned_entity",
                label_ar="فرد خليجي أو منشأة مملوكة بالكامل لمواطني دول مجلس التعاون",
                label_en="GCC person or wholly GCC-owned entity",
            ),
            AuthoredOption(
                value="foreign_legal_entity_or_mixed_foreign_ownership",
                label_ar="جهة أجنبية أو ملكية مختلطة تشمل مستثمراً أجنبياً",
                label_en="Foreign legal entity or mixed ownership including a foreign investor",
            ),
            AuthoredOption(
                value="premium_residency_individual",
                label_ar="فرد يحمل الإقامة المميزة",
                label_en="Premium Residency holder",
            ),
            AuthoredOption(
                value="other",
                label_ar="حالة ملكية أخرى",
                label_en="Other ownership situation",
            ),
        ),
    ),
    "planned_legal_form": AuthoredQuestion(
        question_ar="ما الشكل القانوني الذي تنوي استخدامه؟",
        question_en="Which legal form do you plan to use?",
        help_text_ar=(
            "مثل مؤسسة فردية أو شركة ذات مسؤولية محدودة. إذا لم تحدد الشكل القانوني بعد، "
            "اختر «لم أحدد بعد»."
        ),
        help_text_en=(
            "For example, an individual establishment or a limited liability company. "
            "If you have not chosen yet, select “Not decided yet”."
        ),
        unknown_label_ar="لم أحدد بعد",
        unknown_label_en="Not decided yet",
        options=(
            AuthoredOption(
                value="individual_establishment",
                label_ar="مؤسسة فردية",
                label_en="Individual establishment",
            ),
            AuthoredOption(
                value="limited_liability_company",
                label_ar="شركة ذات مسؤولية محدودة",
                label_en="Limited liability company",
            ),
            AuthoredOption(
                value="other",
                label_ar="شكل قانوني آخر",
                label_en="Another legal form",
            ),
        ),
    ),
    "has_selected_business_premises": AuthoredQuestion(
        question_ar="هل اخترت موقعًا للمشروع؟",
        question_en="Have you chosen premises for the business?",
        help_text_ar=(
            "لا تحتاج إلى إدخال عنوان. اختر «نعم» إذا لديك موقع محدد أو موقع مرشح "
            "وتريد معرفة أين تتحقق من ملاءمته للنشاط."
        ),
        help_text_en=(
            "Do not enter an address. Choose “Yes” if you have selected or shortlisted "
            "premises and want to know where to verify activity suitability."
        ),
    ),
    "gosi_coverage_conditions_met": AuthoredQuestion(
        question_ar="هل تم التأكد من تحقق شروط الخضوع الرسمية للتأمينات الاجتماعية؟",
        question_en="Have the applicable official GOSI coverage conditions been confirmed?",
        help_text_ar="اختر غير معروف إذا لم يتم التأكد من الشروط الرسمية المنطبقة.",
        help_text_en=(
            "Choose unknown if the applicable official conditions have not been confirmed."
        ),
    ),
    "has_employees": AuthoredQuestion(
        question_ar="هل ستوظف موظفين أو عمالًا للعمل في المنشأة؟",
        question_en="Will the business employ staff or workers?",
        help_text_ar=(
            "المقصود موظفو المنشأة وعمالها، وليس عمال شركات التوصيل أو المقاولين الخارجيين."
        ),
        help_text_en=(
            "This means people employed by the business, not third-party delivery "
            "workers or external contractors."
        ),
    ),
    "has_food_establishment_workers": AuthoredQuestion(
        question_ar="هل سيعمل موظفون أو عمال داخل منشأة الطعام أو المشروبات؟",
        question_en="Will staff or workers work in the food or beverage establishment?",
        help_text_ar="المقصود الأشخاص الذين سيعملون داخل نشاط الطعام أو المشروبات عند بدء التشغيل.",
        help_text_en=(
            "This means people who will work inside the food or beverage business "
            "when it starts operating."
        ),
    ),
    "zatca_confirmed_mandatory_vat_registration_applies": AuthoredQuestion(
        question_ar=(
            "بعد التحقق عبر المسار الرسمي لهيئة الزكاة والضريبة والجمارك، "
            "ما حالة التسجيل الإلزامي في ضريبة القيمة المضافة لمنشأتك؟"
        ),
        question_en=(
            "After checking through ZATCA’s official route, what is the mandatory "  # noqa: RUF001
            "VAT registration status for your business?"
        ),
        help_text_ar=(
            "اختر «إلزامي» أو «غير إلزامي» فقط إذا تأكدت من حالة منشأتك عبر المسار "
            "الرسمي للهيئة. إذا لم تتحقق، أو بقيت الحالة غير واضحة، اختر «لم أتأكد "
            "عبر الهيئة بعد». لا يحسب الدليل الإيرادات أو التوريدات، ولا يحدد الحدود "
            "أو الاستثناءات، ولا يحول التسجيل الاختياري إلى التزام."
        ),
        help_text_en=(
            "Choose “Mandatory” or “Not mandatory” only after confirming the business’s "  # noqa: RUF001
            "status through ZATCA’s official route. If you have not checked or the status "  # noqa: RUF001
            "remains unclear, choose “I have not confirmed through ZATCA yet.” The Navigator "
            "does not calculate revenue or supplies, determine thresholds or exceptions, "
            "or turn optional registration into an obligation."
        ),
        true_label_ar="تأكدت عبر الهيئة أنه إلزامي",
        true_label_en="I confirmed through ZATCA that it is mandatory",
        false_label_ar="تأكدت عبر الهيئة أنه غير إلزامي",
        false_label_en="I confirmed through ZATCA that it is not mandatory",
        unknown_label_ar="لم أتأكد عبر الهيئة بعد",
        unknown_label_en="I have not confirmed through ZATCA yet",
    ),
    "offers_home_delivery": AuthoredQuestion(
        question_ar="هل ستقدم المنشأة خدمة التوصيل المنزلي؟",
        question_en="Will the establishment offer home delivery?",
        help_text_ar="المقصود توصيل طلبات المنشأة إلى العملاء.",
        help_text_en="This means delivering the business's orders to customers.",
    ),
    "uses_public_sidewalk_for_customer_service": AuthoredQuestion(
        question_ar="هل ستستخدم الرصيف العام أمام المطعم لخدمة العملاء؟",
        question_en=(
            "Will the restaurant use the public sidewalk opposite the premises for customer "
            "service?"
        ),
        help_text_ar=(
            "المقصود الجزء العام خارج حدود موقعك المرخص، وليس المساحة الخاصة داخل المنشأة."
        ),
        help_text_en=(
            "This means public space outside the licensed premises, not private "
            "space inside the business."
        ),
    ),
}


__all__ = ["QUESTION_TEXT", "AuthoredOption", "AuthoredQuestion"]
