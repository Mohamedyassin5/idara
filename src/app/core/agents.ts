import { IconName } from './icon';
import { L } from './i18n';

/** One field of an agent's quick form. `geo` renders latitude + longitude and a "my location" button. */
export interface FormField {
  key: string;
  type: 'text' | 'select' | 'geo';
  label: L;
  placeholder?: L;
  options?: L[]; // select only: the option label (in the current language) is what gets inserted in the question
  defaultValue?: L;
}

export interface AgentForm {
  title: L;
  fields: FormField[];
  /** Question template; {key} placeholders are replaced by the field values ({lat}/{lng} for geo). */
  template: L;
}

export interface AgentConfig {
  slug: string; // URL segment: /agent/:slug
  backendId: string; // agent id in the backend (agents/*/*_agent.py), used to check who answered
  hubId: string;
  icon: IconName;
  accent: string; // CSS colour driving the page theme
  ready: boolean; // false for placeholder agents (kotob, benevolat)
  name: L;
  description: L;
  prompts: L[];
  form?: AgentForm;
}

export interface HubConfig {
  id: string; // hub id in the backend (agents/hubs.py)
  icon: IconName;
  accent: string;
  name: L;
  description: L;
}

// Tunisian-inspired palette (Sidi Bou Saïd blue, flag red, ochre, olive), brightened for the black theme.
const BLUE = '#5b9bea';
const RED = '#f0605a';
const OCHRE = '#e8954f';
const GREEN = '#4fbf8c';

export const HUBS: HubConfig[] = [
  {
    id: 'admin-utilities-hub',
    icon: 'landmark',
    accent: BLUE,
    name: { fr: 'Administration & Services', ar: 'الإدارة والخدمات', en: 'Administration & Utilities' },
    description: {
      fr: 'Papiers, démarches, STEG/SONEDE et création d’entreprise.',
      ar: 'الوثائق والإجراءات والستاغ والصوناد وبعث المؤسسات.',
      en: 'Documents, procedures, STEG/SONEDE and starting a business.',
    },
  },
  {
    id: 'mobility-city-hub',
    icon: 'pin',
    accent: OCHRE,
    name: { fr: 'Mobilité & Ville', ar: 'التنقل والمدينة', en: 'Mobility & City' },
    description: {
      fr: 'Louage et transport, stationnement, souks et marchés.',
      ar: 'اللواج والنقل والوقوف والأسواق.',
      en: 'Louage and transport, parking, souks and markets.',
    },
  },
  {
    id: 'education-work-hub',
    icon: 'openbook',
    accent: RED,
    name: { fr: 'Éducation & Emploi', ar: 'التعليم والشغل', en: 'Education & Work' },
    description: {
      fr: 'Bac et orientation, recherche d’emploi, livres scolaires.',
      ar: 'الباكالوريا والتوجيه والبحث عن شغل والكتب المدرسية.',
      en: 'Baccalaureate and orientation, job hunting, school books.',
    },
  },
  {
    id: 'housing-community-hub',
    icon: 'people',
    accent: GREEN,
    name: { fr: 'Logement & Communauté', ar: 'السكن والمجتمع', en: 'Housing & Community' },
    description: {
      fr: 'Location et achat, bénévolat et associations.',
      ar: 'الكراء والشراء والتطوع والجمعيات.',
      en: 'Renting and buying, volunteering and associations.',
    },
  },
];

export const AGENTS: AgentConfig[] = [
  {
    slug: 'bureaucratie',
    backendId: 'bureaucratie-agent',
    hubId: 'admin-utilities-hub',
    icon: 'document',
    accent: BLUE,
    ready: true,
    name: { fr: 'Démarches administratives', ar: 'الإجراءات الإدارية', en: 'Administrative procedures' },
    description: {
      fr: 'Carte d’identité, passeport, extrait de naissance, CNSS, carte grise, permis.',
      ar: 'بطاقة التعريف، جواز السفر، مضمون الولادة، الضمان الاجتماعي، البطاقة الرمادية، رخصة السياقة.',
      en: 'ID card, passport, birth certificate, CNSS, vehicle registration, driving licence.',
    },
    prompts: [
      {
        fr: 'Quels papiers faut-il pour renouveler ma carte d’identité ?',
        ar: 'شنوة الوثائق المطلوبة لتجديد بطاقة التعريف؟',
        en: 'Which documents do I need to renew my ID card?',
      },
      {
        fr: 'Comment obtenir un extrait de naissance ?',
        ar: 'كيفاش نخرّج مضمون ولادة؟',
        en: 'How do I get a birth certificate?',
      },
      {
        fr: 'Comment renouveler mon permis de conduire ?',
        ar: 'كيفاش نجدّد رخصة السياقة؟',
        en: 'How do I renew my driving licence?',
      },
    ],
  },
  {
    slug: 'steg',
    backendId: 'steg-agent',
    hubId: 'admin-utilities-hub',
    icon: 'bolt',
    accent: '#e0b048',
    ready: true,
    name: { fr: 'STEG & SONEDE', ar: 'الستاغ والصوناد', en: 'STEG & SONEDE' },
    description: {
      fr: 'Factures d’électricité, gaz et eau, coupures, contestation, abonnement.',
      ar: 'فواتير الكهرباء والغاز والماء، الانقطاعات، الاعتراض، الاشتراك.',
      en: 'Electricity, gas and water bills, outages, disputes, subscriptions.',
    },
    prompts: [
      {
        fr: 'Comment payer ma facture STEG en ligne ?',
        ar: 'كيفاش نخلّص فاتورة الستاغ أونلاين؟',
        en: 'How can I pay my STEG bill online?',
      },
      {
        fr: 'Ma facture d’électricité est trop élevée, comment la contester ?',
        ar: 'فاتورة الكهرباء غالية برشا، كيفاش نعترض عليها؟',
        en: 'My electricity bill is too high, how do I dispute it?',
      },
      {
        fr: 'Comment signaler une coupure de courant ?',
        ar: 'كيفاش نبلّغ على انقطاع الضو؟',
        en: 'How do I report a power outage?',
      },
    ],
  },
  {
    slug: 'entrepreneuriat',
    backendId: 'entrepreneuriat-agent',
    hubId: 'admin-utilities-hub',
    icon: 'rocket',
    accent: '#a98be6',
    ready: true,
    name: { fr: 'Entrepreneuriat', ar: 'بعث المشاريع', en: 'Entrepreneurship' },
    description: {
      fr: 'Formes juridiques, étapes d’enregistrement, autorisations, structures d’appui.',
      ar: 'الأشكال القانونية، خطوات التسجيل، التراخيص، هياكل المرافقة.',
      en: 'Legal forms, registration steps, permits, support organisations.',
    },
    prompts: [
      {
        fr: 'Quelle forme juridique choisir pour lancer mon activité ?',
        ar: 'أي شكل قانوني نختار باش نبعث مشروعي؟',
        en: 'Which legal form should I choose to start my business?',
      },
      {
        fr: 'Quelles sont les étapes pour enregistrer une activité ?',
        ar: 'شنوة خطوات تسجيل نشاط؟',
        en: 'What are the steps to register a business?',
      },
      {
        fr: 'Où trouver un accompagnement pour entrepreneurs ?',
        ar: 'وين نلقى مرافقة لأصحاب المشاريع؟',
        en: 'Where can I find support for entrepreneurs?',
      },
    ],
  },
  {
    slug: 'louage',
    backendId: 'louage-agent',
    hubId: 'mobility-city-hub',
    icon: 'van',
    accent: OCHRE,
    ready: true,
    name: { fr: 'Louage & transport', ar: 'اللواج والنقل', en: 'Louage & transport' },
    description: {
      fr: 'Stations, tarifs indicatifs, louage, bus, métro, train et taxi.',
      ar: 'المحطات، الأسعار التقريبية، اللواج، الحافلة، المترو، القطار والتاكسي.',
      en: 'Stations, indicative fares, louage, bus, metro, train and taxi.',
    },
    prompts: [
      {
        fr: 'Comment fonctionne un louage ?',
        ar: 'كيفاش يخدم اللواج؟',
        en: 'How does a louage work?',
      },
      {
        fr: 'Louage ou train : que choisir pour un long trajet ?',
        ar: 'لواج ولا ترام: شنوة نختار لمسافة طويلة؟',
        en: 'Louage or train: which one for a long trip?',
      },
      {
        fr: 'Quelles règles respecter en tant que passager ?',
        ar: 'شنوة القواعد اللي لازم نحترمها كراكب؟',
        en: 'What rules should passengers follow?',
      },
      {
        fr: 'Quelles stations de louage y a-t-il à Tunis ?',
        ar: 'شنوة محطات اللواج الموجودة في تونس؟',
        en: 'Which louage stations are there in Tunis?',
      },
    ],
    form: {
      title: { fr: 'Planifier un trajet', ar: 'تخطيط رحلة', en: 'Plan a trip' },
      fields: [
        {
          key: 'from',
          type: 'text',
          label: { fr: 'Départ', ar: 'الانطلاق', en: 'From' },
          placeholder: { fr: 'ex. Tunis', ar: 'مثلا تونس', en: 'e.g. Tunis' },
        },
        {
          key: 'to',
          type: 'text',
          label: { fr: 'Arrivée', ar: 'الوصول', en: 'To' },
          placeholder: { fr: 'ex. Sousse', ar: 'مثلا سوسة', en: 'e.g. Sousse' },
        },
      ],
      template: {
        fr: 'Je dois aller de {from} à {to} en transport collectif : où embarquer et à peu près combien ça coûte ?',
        ar: 'لازم نمشي من {from} إلى {to} بالنقل الجماعي: وين نركب وقداش تقريبا الثمن؟',
        en: 'I need to go from {from} to {to} by shared transport: where do I board and roughly how much does it cost?',
      },
    },
  },
  {
    slug: 'parking',
    backendId: 'parking-agent',
    hubId: 'mobility-city-hub',
    icon: 'parking',
    accent: '#74aaea',
    ready: true,
    name: { fr: 'Stationnement', ar: 'الوقوف', en: 'Parking' },
    description: {
      fr: 'Zones payantes, paiement, tarifs indicatifs, contravention et fourrière.',
      ar: 'مناطق الوقوف المدفوعة، الدفع، الأسعار التقريبية، المخالفات والحجز.',
      en: 'Paid zones, payment, indicative rates, fines and towing.',
    },
    prompts: [
      {
        fr: 'Comment payer le stationnement dans la rue ?',
        ar: 'كيفاش نخلّص الباركينغ في الشارع؟',
        en: 'How do I pay for street parking?',
      },
      {
        fr: 'Ma voiture a été mise en fourrière, comment la récupérer ?',
        ar: 'كرهبتي مشات للفوريار، كيفاش نرجّعها؟',
        en: 'My car was towed, how do I get it back?',
      },
      {
        fr: 'Où trouver un parking couvert ?',
        ar: 'وين نلقى باركينغ مغطّى؟',
        en: 'Where can I find a covered car park?',
      },
    ],
    form: {
      title: { fr: 'Parkings autour de moi', ar: 'مواقف قريبة مني', en: 'Parkings near me' },
      fields: [{ key: 'geo', type: 'geo', label: { fr: 'Coordonnées', ar: 'الإحداثيات', en: 'Coordinates' } }],
      template: {
        fr: 'Quels parkings sont repérés autour de ma position (latitude {lat}, longitude {lng}) ? Montre-les sur la carte.',
        ar: 'شنوة المواقف القريبة من موقعي (خط العرض {lat}، خط الطول {lng})؟ ورّيهم على الخريطة.',
        en: 'Which car parks are nearby my position (latitude {lat}, longitude {lng})? Show them on the map.',
      },
    },
  },
  {
    slug: 'souk',
    backendId: 'souk-agent',
    hubId: 'mobility-city-hub',
    icon: 'market',
    accent: '#e8836a',
    ready: true,
    name: { fr: 'Souks & marchés', ar: 'الأسواق', en: 'Souks & markets' },
    description: {
      fr: 'Négociation, prix, souk ou supermarché, conseils pour bien acheter.',
      ar: 'المفاوضة، الأسعار، السوق ولا السوبر ماركت، نصائح للشراء.',
      en: 'Haggling, prices, souk or supermarket, buying tips.',
    },
    prompts: [
      {
        fr: 'Comment marchander dans la médina sans payer le prix touriste ?',
        ar: 'كيفاش نفاصل في المدينة العربي بلا ما ندفع سعر السائح؟',
        en: 'How do I haggle in the medina without paying tourist prices?',
      },
      {
        fr: 'Qu’est-ce qui influence les prix au souk ?',
        ar: 'شنوة اللي يأثّر على الأسعار في السوق؟',
        en: 'What influences prices at the souk?',
      },
      {
        fr: 'Souk ou supermarché : que choisir ?',
        ar: 'السوق ولا السوبر ماركت: شنوة نختار؟',
        en: 'Souk or supermarket: which one?',
      },
    ],
    form: {
      title: { fr: 'Marchés autour de moi', ar: 'أسواق قريبة مني', en: 'Markets near me' },
      fields: [{ key: 'geo', type: 'geo', label: { fr: 'Coordonnées', ar: 'الإحداثيات', en: 'Coordinates' } }],
      template: {
        fr: 'Quels souks ou marchés sont repérés autour de ma position (latitude {lat}, longitude {lng}) ? Montre-les sur la carte.',
        ar: 'شنوة الأسواق القريبة من موقعي (خط العرض {lat}، خط الطول {lng})؟ ورّيهم على الخريطة.',
        en: 'Which souks or markets are nearby my position (latitude {lat}, longitude {lng})? Show them on the map.',
      },
    },
  },
  {
    slug: 'bac',
    backendId: 'bac-agent',
    hubId: 'education-work-hub',
    icon: 'graduation',
    accent: RED,
    ready: true,
    name: { fr: 'Bac & orientation', ar: 'الباك والتوجيه', en: 'Bac & orientation' },
    description: {
      fr: 'Structure du bac, calcul de la moyenne, orientation, filières, méthode de révision.',
      ar: 'هيكلة الباكالوريا، احتساب المعدل، التوجيه، الشعب، طرق المراجعة.',
      en: 'Bac structure, grade calculation, orientation, degree paths, revision tips.',
    },
    prompts: [
      {
        fr: 'Comment est calculée la moyenne du bac ?',
        ar: 'كيفاش يتحسب معدل الباك؟',
        en: 'How is the bac average calculated?',
      },
      {
        fr: 'Comment fonctionne l’orientation universitaire ?',
        ar: 'كيفاش يخدم التوجيه الجامعي؟',
        en: 'How does university orientation work?',
      },
      {
        fr: 'Des conseils pour bien réviser le bac ?',
        ar: 'عندك نصائح باش نراجع مليح للباك؟',
        en: 'Any tips to revise well for the bac?',
      },
    ],
  },
  {
    slug: 'job',
    backendId: 'job-agent',
    hubId: 'education-work-hub',
    icon: 'briefcase',
    accent: '#45c1cf',
    ready: true,
    name: { fr: 'Emploi & stages', ar: 'الشغل والتربصات', en: 'Jobs & internships' },
    description: {
      fr: 'CV, entretien, contrats, droits du salarié, repérage de commerces pour candidature spontanée.',
      ar: 'السيرة الذاتية، المقابلة، العقود، حقوق الأجير، تحديد المحلات للترشح التلقائي.',
      en: 'CV, interviews, contracts, employee rights, spotting businesses for spontaneous applications.',
    },
    prompts: [
      {
        fr: 'Comment rédiger un CV efficace ?',
        ar: 'كيفاش نكتب سيرة ذاتية مليحة؟',
        en: 'How do I write an effective CV?',
      },
      {
        fr: 'Comment préparer un entretien d’embauche ?',
        ar: 'كيفاش نستعد لمقابلة عمل؟',
        en: 'How do I prepare for a job interview?',
      },
      {
        fr: 'Quelle différence entre CDI et CDD ?',
        ar: 'شنوة الفرق بين CDI و CDD؟',
        en: 'What is the difference between a CDI and a CDD?',
      },
    ],
  },
  {
    slug: 'immobilier',
    backendId: 'immobilier-agent',
    hubId: 'housing-community-hub',
    icon: 'home',
    accent: GREEN,
    ready: true,
    name: { fr: 'Immobilier', ar: 'العقارات', en: 'Real estate' },
    description: {
      fr: 'Location, achat, contrat de bail, frais, arnaques courantes, documents.',
      ar: 'الكراء، الشراء، عقد الكراء، المصاريف، الاحتيال الشائع، الوثائق.',
      en: 'Renting, buying, lease contracts, fees, common scams, documents.',
    },
    prompts: [
      {
        fr: 'Comment repérer les fausses annonces immobilières ?',
        ar: 'كيفاش نعرف الإعلانات العقارية المزيّفة؟',
        en: 'How do I spot fake property listings?',
      },
      {
        fr: 'Quels éléments doit contenir un contrat de location ?',
        ar: 'شنوة لازم يحتوي عقد الكراء؟',
        en: 'What must a rental contract include?',
      },
      {
        fr: 'Quels frais prévoir quand on loue ?',
        ar: 'شنوة المصاريف اللي لازم نحسب لها عند الكراء؟',
        en: 'What costs should I expect when renting?',
      },
      {
        fr: 'Compare le loyer moyen entre quelques quartiers de Tunis',
        ar: 'قارن الكراء المتوسط بين شوية أحياء في تونس',
        en: 'Compare the average rent across a few Tunis neighbourhoods',
      },
    ],
    form: {
      title: { fr: 'Chercher un logement', ar: 'البحث عن سكن', en: 'Find a home' },
      fields: [
        {
          key: 'mode',
          type: 'select',
          label: { fr: 'Je veux', ar: 'نحب', en: 'I want to' },
          options: [
            { fr: 'louer', ar: 'نكري', en: 'rent' },
            { fr: 'acheter', ar: 'نشري', en: 'buy' },
          ],
        },
        {
          key: 'city',
          type: 'text',
          label: { fr: 'Ville', ar: 'المدينة', en: 'City' },
          placeholder: { fr: 'ex. Sousse', ar: 'مثلا سوسة', en: 'e.g. Sousse' },
        },
      ],
      template: {
        fr: 'Je veux {mode} un logement à {city} : par où commencer et comment éviter les arnaques ?',
        ar: 'نحب {mode} دار في {city}: من وين نبدأ وكيفاش نتجنب الاحتيال؟',
        en: 'I want to {mode} a home in {city}: where do I start and how do I avoid scams?',
      },
    },
  },
  {
    slug: 'benevolat',
    backendId: 'benevolat-agent',
    hubId: 'housing-community-hub',
    icon: 'heart',
    accent: '#f2844f',
    ready: false,
    name: { fr: 'Bénévolat & associations', ar: 'التطوع والجمعيات', en: 'Volunteering & associations' },
    description: {
      fr: 'S’engager dans des associations et des initiatives citoyennes.',
      ar: 'الانخراط في الجمعيات والمبادرات المواطنية.',
      en: 'Getting involved in associations and citizen initiatives.',
    },
    prompts: [
      {
        fr: 'Comment m’engager comme bénévole dans mon quartier ?',
        ar: 'كيفاش نتطوع في حومتي؟',
        en: 'How can I volunteer in my neighbourhood?',
      },
    ],
  },
];

export const agentBySlug = (slug: string): AgentConfig | undefined => AGENTS.find((a) => a.slug === slug);
export const agentByBackendId = (id: string): AgentConfig | undefined => AGENTS.find((a) => a.backendId === id);
export const agentsOfHub = (hubId: string): AgentConfig[] => AGENTS.filter((a) => a.hubId === hubId);
