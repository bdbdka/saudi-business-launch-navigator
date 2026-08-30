import type { ActivityCode } from "@/lib/api/types";

export const BALADY_ACTIVITY_HOSTNAME = "services.balady.gov.sa";

export type OfficialActivityReference = Readonly<{
  activityCode: ActivityCode;
  activityId: string;
  titleAr: string;
  titleEn: string;
  authorityAr: string;
  authorityEn: string;
  platformAr: string;
  platformEn: string;
  officialUrl: string;
}>;

type OfficialActivityReferenceMap = {
  readonly [Code in ActivityCode]: OfficialActivityReference & {
    readonly activityCode: Code;
  };
};

export const officialActivityReferences = {
  coffee_shop: {
    activityCode: "coffee_shop",
    activityId: "1770",
    titleAr: "محلات تقديم المشروبات الكوفي شوب",
    titleEn: "Coffee shop",
    authorityAr: "وزارة البلديات والإسكان",
    authorityEn: "Ministry of Municipalities and Housing",
    platformAr: "منصة بلدي",
    platformEn: "Balady",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1770",
  },
  restaurant: {
    activityCode: "restaurant",
    activityId: "1319",
    titleAr: "المطاعم مع الخدمة",
    titleEn: "Restaurant with service",
    authorityAr: "وزارة البلديات والإسكان",
    authorityEn: "Ministry of Municipalities and Housing",
    platformAr: "منصة بلدي",
    platformEn: "Balady",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=1319",
  },
  cloud_kitchen: {
    activityCode: "cloud_kitchen",
    activityId: "859397",
    titleAr: "المطاعم السحابية لأنشطة تقديم الوجبات فقط تناول الوجبة خارج المحل Take Out",
    titleEn: "Cloud kitchen for take-out meal preparation",
    authorityAr: "وزارة البلديات والإسكان",
    authorityEn: "Ministry of Municipalities and Housing",
    platformAr: "منصة بلدي",
    platformEn: "Balady",
    officialUrl:
      "https://services.balady.gov.sa/commercial/inquiry/ActivitiesInquiry/GetDetails?type=detailed&activityId=859397",
  },
} as const satisfies OfficialActivityReferenceMap;

export function officialActivityReference(
  activityCode: ActivityCode,
): OfficialActivityReference | null {
  if (!Object.hasOwn(officialActivityReferences, activityCode)) return null;
  return officialActivityReferences[activityCode];
}

export function safeActivityReferenceUrl(
  reference: OfficialActivityReference,
): string | null {
  try {
    const url = new URL(reference.officialUrl);
    if (
      url.protocol !== "https:"
      || url.username
      || url.password
      || url.hostname !== BALADY_ACTIVITY_HOSTNAME
      || url.pathname !== "/commercial/inquiry/ActivitiesInquiry/GetDetails"
      || url.searchParams.size !== 2
      || url.searchParams.get("type") !== "detailed"
      || url.searchParams.get("activityId") !== reference.activityId
    ) {
      return null;
    }
    return url.toString();
  } catch {
    return null;
  }
}
