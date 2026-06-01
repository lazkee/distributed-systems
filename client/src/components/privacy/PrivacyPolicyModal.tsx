import { useEffect } from "react";

interface PrivacyPolicyModalProps {
  onClose: () => void;
}

export function PrivacyPolicyModal({ onClose }: PrivacyPolicyModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-gray-800 border border-gray-700 rounded-2xl shadow-2xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-gray-100">Privacy Notice</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close privacy notice"
            className="text-gray-400 hover:text-white transition-colors text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="space-y-5 text-sm text-gray-300">
          <section>
            <h3 className="font-semibold text-gray-100 mb-1">What data we collect</h3>
            <p>
              When you register, we collect your first name, last name, email address,
              country, and a password stored as a secure hash. You may optionally upload
              a profile picture.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Why we collect it</h3>
            <p>
              We use your data to authenticate you, personalise your experience, and
              record your quiz participation. No data is shared with third parties for
              advertising purposes.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Authentication and cookies</h3>
            <p>
              We use secure, HTTP-only cookies to manage your session. These cookies are
              strictly necessary for the application to work and are not used for
              advertising or third-party tracking.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Quiz attempts and reports</h3>
            <p>
              We record your quiz attempts, including start and finish times, scores, and
              time taken. This data is used to generate leaderboards and performance
              reports visible to moderators and administrators.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Profile pictures</h3>
            <p>
              If you upload a profile picture, it is stored securely via Cloudinary.
              Erasing your account removes the stored image.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Data export</h3>
            <p>
              You can export all personal data we hold about you at any time from the{" "}
              <strong className="text-gray-100">Profile</strong> page. The export
              includes your profile information and quiz attempt history as a JSON file.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Account erasure and anonymisation</h3>
            <p>
              You can erase your account at any time from the{" "}
              <strong className="text-gray-100">Profile</strong> page. Erasure
              anonymises your personal details — your name, email address, and profile
              picture are removed. Technical quiz attempt records (scores, times) may be
              retained for statistical integrity but will no longer be linked to your
              personal information where technically possible.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Data retention</h3>
            <p>
              Quiz attempt records are automatically deleted after 730 days (2 years).
              Account data is retained until you request erasure.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-gray-100 mb-1">Contact</h3>
            <p>
              This is a university student project. For any questions about your personal
              data, please contact the platform administrator trough the email address mlazic371@gmail.com.
            </p>
          </section>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-all duration-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
