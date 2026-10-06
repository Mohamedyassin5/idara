import { Injectable, computed, effect, signal } from '@angular/core';

export type Lang = 'fr' | 'ar' | 'en';
/** A text available in the three interface languages. */
export type L = Record<Lang, string>;

export const LANGS: { code: Lang; label: string }[] = [
  { code: 'fr', label: 'FR' },
  { code: 'ar', label: 'العربية' },
  { code: 'en', label: 'EN' },
];

const STORAGE_KEY = 'idara.lang';

/** Static interface strings. Keys are looked up with I18n.t(key). */
export const UI = {
  appName: { fr: 'Idara', ar: 'إدارة', en: 'Idara' },
  tagline: {
    fr: 'Votre assistant du quotidien en Tunisie',
    ar: 'مساعدك اليومي في تونس',
    en: 'Your everyday assistant in Tunisia',
  },
  heroTitle: {
    fr: 'Aslema ! Comment puis-je vous aider aujourd’hui ?', // non-breaking spaces: no line break before ! and ?
    ar: 'عسلامة! كيفاش نجم نعاونك اليوم؟',
    en: 'Aslema! How can I help you today?',
  },
  heroSub: {
    fr: 'Démarches, transport, études, emploi, logement : posez votre question en français, en arabe ou en derja.',
    ar: 'إجراءات إدارية، نقل، دراسة، شغل، سكن: اسأل بالفرنسية أو بالعربية أو بالدارجة.',
    en: 'Paperwork, transport, studies, jobs, housing: ask in French, Arabic or Tunisian dialect.',
  },
  askAnything: {
    fr: 'Posez n’importe quelle question…',
    ar: 'اسأل أي سؤال…',
    en: 'Ask anything…',
  },
  askAssistant: { fr: 'Demander à l’assistant', ar: 'اسأل المساعد', en: 'Ask the assistant' },
  orbitCaption: {
    fr: '1 orchestrateur · {h} domaines · {a} agents',
    ar: 'منسّق واحد · {h} مجالات · {a} وكيلا',
    en: '1 orchestrator · {h} domains · {a} agents',
  },
  domains: { fr: 'Choisissez un domaine', ar: 'اختر مجالا', en: 'Pick a domain' },
  soon: { fr: 'Bientôt', ar: 'قريبا', en: 'Soon' },
  soonNote: {
    fr: 'Ce module n’est pas encore disponible : l’agent répondra qu’il n’est pas implémenté.',
    ar: 'هذه الخدمة غير متوفرة بعد: سيجيب الوكيل بأنها غير مفعّلة.',
    en: 'This module is not available yet: the agent will answer that it is not implemented.',
  },
  back: { fr: 'Accueil', ar: 'الرئيسية', en: 'Home' },
  send: { fr: 'Envoyer', ar: 'إرسال', en: 'Send' },
  placeholder: { fr: 'Écrivez votre question…', ar: 'اكتب سؤالك…', en: 'Type your question…' },
  suggestions: { fr: 'Questions fréquentes', ar: 'أسئلة شائعة', en: 'Common questions' },
  quickForm: { fr: 'Formulaire rapide', ar: 'نموذج سريع', en: 'Quick form' },
  ask: { fr: 'Poser la question', ar: 'اطرح السؤال', en: 'Ask' },
  thinking: { fr: 'L’assistant réfléchit…', ar: 'المساعد يفكّر…', en: 'The assistant is thinking…' },
  answeredBy: { fr: 'Réponse de', ar: 'الجواب من', en: 'Answered by' },
  routedElsewhere: {
    fr: 'Cette question a été traitée par un autre domaine.',
    ar: 'تمت معالجة هذا السؤال من مجال آخر.',
    en: 'This question was handled by another domain.',
  },
  newChat: { fr: 'Nouvelle conversation', ar: 'محادثة جديدة', en: 'New conversation' },
  mapEmptyTitle: { fr: 'Aucun résultat pour l’instant', ar: 'مافماش نتيجة توا', en: 'No result yet' },
  mapEmptySub: {
    fr: 'Posez une question ci-dessus : le résultat s’affichera ici, sur la carte.',
    ar: 'اطرح سؤالا فوق: النتيجة تظهر هوني، على الخريطة.',
    en: 'Ask a question above: the result will appear here, on the map.',
  },
  youAsked: { fr: 'Votre question', ar: 'سؤالك', en: 'Your question' },
  convTitle: { fr: 'Conversations', ar: 'المحادثات', en: 'Conversations' },
  convNew: { fr: 'Nouvelle conversation', ar: 'محادثة جديدة', en: 'New conversation' },
  convPinned: { fr: 'Épinglées', ar: 'مثبّتة', en: 'Pinned' },
  convRecent: { fr: 'Récentes', ar: 'الأخيرة', en: 'Recent' },
  convArchived: { fr: 'Archives', ar: 'الأرشيف', en: 'Archive' },
  convEmpty: { fr: 'Aucune conversation pour l’instant.', ar: 'مافماش محادثات توا.', en: 'No conversations yet.' },
  convPin: { fr: 'Épingler', ar: 'تثبيت', en: 'Pin' },
  convUnpin: { fr: 'Désépingler', ar: 'إلغاء التثبيت', en: 'Unpin' },
  convArchive: { fr: 'Archiver', ar: 'أرشفة', en: 'Archive' },
  convUnarchive: { fr: 'Désarchiver', ar: 'إلغاء الأرشفة', en: 'Unarchive' },
  convDelete: { fr: 'Supprimer', ar: 'حذف', en: 'Delete' },
  convDeleteConfirm: { fr: 'Supprimer cette conversation ? Cette action est définitive.', ar: 'تحذف هالمحادثة؟ ما فماش رجعة.', en: 'Delete this conversation? This cannot be undone.' },
  convOpen: { fr: 'Ouvrir', ar: 'فتح', en: 'Open' },
  cvTitle: { fr: 'Votre CV', ar: 'سيرتك الذاتية', en: 'Your CV' },
  you: { fr: 'Vous', ar: 'أنت', en: 'You' },
  myLocation: { fr: 'Ma position', ar: 'موقعي', en: 'My location' },
  locating: { fr: 'Localisation…', ar: 'تحديد الموقع…', en: 'Locating…' },
  locationDenied: {
    fr: 'Position indisponible : saisissez les coordonnées à la main.',
    ar: 'تعذّر تحديد الموقع: أدخل الإحداثيات يدويا.',
    en: 'Location unavailable: enter the coordinates manually.',
  },
  errorBackend: {
    fr: 'Impossible de joindre le serveur. Vérifiez que le backend est démarré (python -m app.main ou docker compose), puis réessayez.',
    ar: 'تعذّر الاتصال بالخادم. تأكد أن الخادم يعمل (python -m app.main أو docker compose) ثم أعد المحاولة.',
    en: 'Cannot reach the server. Make sure the backend is running (python -m app.main or docker compose), then try again.',
  },
  errorGeneric: {
    fr: 'Une erreur est survenue. Réessayez dans un instant.',
    ar: 'حدث خطأ. أعد المحاولة بعد قليل.',
    en: 'Something went wrong. Please try again shortly.',
  },
  notFound: { fr: 'Page introuvable', ar: 'الصفحة غير موجودة', en: 'Page not found' },
  footer: {
    fr: 'Informations générales et indicatives, non officielles. Vérifiez toujours auprès de l’organisme concerné.',
    ar: 'معلومات عامة وإرشادية وغير رسمية. تحقق دائما لدى الجهة المعنية.',
    en: 'General, indicative and unofficial information. Always check with the relevant authority.',
  },
  madeIn: { fr: 'Fait en Tunisie', ar: 'صُنع في تونس', en: 'Made in Tunisia' },
  assistantName: { fr: 'Assistant Idara', ar: 'مساعد إدارة', en: 'Idara assistant' },
  assistantDesc: {
    fr: 'Posez votre question : l’orchestrateur choisit automatiquement le bon domaine.',
    ar: 'اطرح سؤالك: يختار المنسّق تلقائيا المجال المناسب.',
    en: 'Ask your question: the orchestrator automatically picks the right domain.',
  },
  landingSlogan: {
    fr: 'La Tunisie, simplifiée.',
    ar: 'تونس، أبسط.',
    en: 'Tunisia, made simple.',
  },
  landingSub: {
    fr: 'Démarches, transport, études, emploi, logement : un seul assistant, en français, en arabe et en derja.',
    ar: 'إجراءات، نقل، دراسة، شغل، سكن: مساعد واحد، بالفرنسية وبالعربية وبالدارجة.',
    en: 'Paperwork, transport, studies, jobs, housing: one assistant, in French, Arabic and Tunisian dialect.',
  },
  landingStart: { fr: 'Commencer', ar: 'ابدأ', en: 'Get started' },
  landingAsk: { fr: 'Poser une question', ar: 'اطرح سؤالا', en: 'Ask a question' },
  landingWhy: { fr: 'Tout ce dont vous avez besoin, au même endroit', ar: 'كل ما تحتاجه في مكان واحد', en: 'Everything you need, in one place' },
  landingF1t: { fr: 'Administration', ar: 'الإدارة', en: 'Administration' },
  landingF1d: {
    fr: 'Papiers, STEG/SONEDE, création d’entreprise : les étapes claires, sans file d’attente.',
    ar: 'الوثائق، الستاغ والصوناد، بعث مؤسسة: خطوات واضحة دون طوابير.',
    en: 'Documents, utilities, starting a business: clear steps, no queues.',
  },
  landingF2t: { fr: 'Mobilité', ar: 'التنقّل', en: 'Mobility' },
  landingF2d: {
    fr: 'Louage, parking, souks : trouvez votre chemin en ville.',
    ar: 'اللواج، مواقف السيارات، الأسواق: اعرف طريقك في المدينة.',
    en: 'Louage, parking, markets: find your way around the city.',
  },
  landingF3t: { fr: 'Études & emploi', ar: 'الدراسة والشغل', en: 'Studies & work' },
  landingF3d: {
    fr: 'Bac, concours, offres d’emploi : avancez dans votre parcours.',
    ar: 'الباكالوريا، المناظرات، عروض الشغل: تقدّم في مسارك.',
    en: 'Baccalaureate, exams, job offers: move forward in your journey.',
  },
  landingF4t: { fr: 'Logement', ar: 'السكن', en: 'Housing' },
  landingF4d: {
    fr: 'Immobilier, bénévolat, associations : ancrez-vous dans votre communauté.',
    ar: 'العقارات، التطوّع، الجمعيات: اندمج في مجتمعك.',
    en: 'Real estate, volunteering, associations: settle into your community.',
  },
  landingClosing: { fr: 'Une question ? Demandez à Idara.', ar: 'عندك سؤال؟ اسأل إدارة.', en: 'A question? Ask Idara.' },
  login: { fr: 'Se connecter', ar: 'تسجيل الدخول', en: 'Log in' },
  register: { fr: 'Créer un compte', ar: 'إنشاء حساب', en: 'Create account' },
  logout: { fr: 'Déconnexion', ar: 'تسجيل الخروج', en: 'Log out' },
  authSub: {
    fr: 'Connectez-vous pour discuter avec l’assistant.',
    ar: 'سجّل الدخول للتحدث مع المساعد.',
    en: 'Sign in to chat with the assistant.',
  },
  fullName: { fr: 'Nom complet', ar: 'الاسم الكامل', en: 'Full name' },
  email: { fr: 'Adresse e-mail', ar: 'البريد الإلكتروني', en: 'Email address' },
  password: { fr: 'Mot de passe', ar: 'كلمة المرور', en: 'Password' },
  passwordHint: { fr: '8 caractères minimum.', ar: '8 أحرف على الأقل.', en: 'At least 8 characters.' },
  noAccount: { fr: 'Pas encore de compte ?', ar: 'ليس لديك حساب؟', en: 'No account yet?' },
  haveAccount: { fr: 'Déjà un compte ?', ar: 'لديك حساب؟', en: 'Already have an account?' },
  authInvalid: { fr: 'E-mail ou mot de passe incorrect.', ar: 'البريد أو كلمة المرور غير صحيحة.', en: 'Incorrect email or password.' },
  authExists: { fr: 'Cette adresse e-mail est déjà utilisée.', ar: 'هذا البريد مستعمل بالفعل.', en: 'This email is already registered.' },
  authCheckFields: {
    fr: 'Vérifiez les champs (e-mail valide, mot de passe de 8 caractères minimum).',
    ar: 'تحقق من الحقول (بريد صالح وكلمة مرور من 8 أحرف على الأقل).',
    en: 'Check the fields (valid email, password of at least 8 characters).',
  },
} satisfies Record<string, L>;

export type UiKey = keyof typeof UI;

@Injectable({ providedIn: 'root' })
export class I18n {
  readonly lang = signal<Lang>(this.initial());
  readonly dir = computed(() => (this.lang() === 'ar' ? 'rtl' : 'ltr'));

  constructor() {
    effect(() => {
      const lang = this.lang();
      document.documentElement.lang = lang;
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
      try {
        localStorage.setItem(STORAGE_KEY, lang);
      } catch {
        /* storage unavailable: language just won't persist */
      }
    });
  }

  t(key: UiKey): string {
    return UI[key][this.lang()];
  }

  /** Pick the current-language text from a trilingual value. */
  pick(text: L): string {
    return text[this.lang()];
  }

  private initial(): Lang {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'fr' || saved === 'ar' || saved === 'en') return saved;
    } catch {
      /* ignore */
    }
    return 'fr';
  }
}
