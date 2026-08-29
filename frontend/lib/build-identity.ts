export const BUILD_COMMIT_HEADER = "X-SBLN-Build-Commit";

const FULL_GIT_SHA_LENGTH = 40;
const HEXADECIMAL = /^[0-9a-fA-F]+$/;

export function validatedBuildCommit(value: string | undefined): string | null {
  if (value === undefined || value === "") return null;
  if (value.length !== FULL_GIT_SHA_LENGTH || !HEXADECIMAL.test(value)) {
    throw new Error(
      "SBLN_FRONTEND_BUILD_COMMIT must be exactly 40 hexadecimal characters.",
    );
  }
  return value;
}

export function buildCommitHeader(
  value = process.env.SBLN_FRONTEND_BUILD_COMMIT,
): { key: typeof BUILD_COMMIT_HEADER; value: string } | null {
  const commit = validatedBuildCommit(value);
  return commit ? { key: BUILD_COMMIT_HEADER, value: commit } : null;
}
