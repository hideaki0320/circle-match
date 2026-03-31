/**
 * 全大学サークルデータ → all_circles_data.js 変換 (Node.js版)
 * 早稲田 + 他大学(Web) + PDF大学(慶應・東大) を統合
 */
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const SRC_WASEDA = path.join(DIR, 'waseda_circles.json');
const SRC_MULTI  = path.join(DIR, 'multi_univ_circles.json');
const SRC_PDF    = path.join(DIR, 'pdf_univ_circles.json');
const DEST       = path.join(DIR, 'all_circles_data.js');

const GENRE_MAP = {
  baseball:               {cats:["sports"],             scores:{sports:9,culture:1,tech:1,social:5,outdoor:2,creative:1,game:1},intensity:"gachi",vibe:"bright",vertical:true},
  football:               {cats:["sports"],             scores:{sports:9,culture:1,tech:1,social:6,outdoor:2,creative:1,game:1},intensity:"middle",vibe:"bright",vertical:false},
  futsal:                 {cats:["sports"],             scores:{sports:9,culture:1,tech:1,social:6,outdoor:2,creative:1,game:1},intensity:"middle",vibe:"bright",vertical:false},
  basketball:             {cats:["sports"],             scores:{sports:9,culture:1,tech:1,social:5,outdoor:1,creative:1,game:1},intensity:"middle",vibe:"bright",vertical:false},
  tennis:                 {cats:["sports"],             scores:{sports:8,culture:1,tech:1,social:7,outdoor:3,creative:1,game:1},intensity:"middle",vibe:"bright",vertical:false},
  volleyball:             {cats:["sports"],             scores:{sports:8,culture:1,tech:1,social:5,outdoor:1,creative:1,game:1},intensity:"middle",vibe:"bright",vertical:false},
  golf:                   {cats:["sports","outdoor"],   scores:{sports:7,culture:1,tech:1,social:6,outdoor:6,creative:1,game:1},intensity:"yuru",vibe:"cool",vertical:false},
  badminton:              {cats:["sports"],             scores:{sports:8,culture:1,tech:1,social:6,outdoor:1,creative:1,game:1},intensity:"middle",vibe:"cozy",vertical:false},
  dance:                  {cats:["culture"],            scores:{sports:4,culture:10,tech:1,social:7,outdoor:1,creative:5,game:1},intensity:"middle",vibe:"cool",vertical:false},
  "martial-arts":         {cats:["sports"],             scores:{sports:9,culture:3,tech:1,social:4,outdoor:1,creative:1,game:1},intensity:"gachi",vibe:"cozy",vertical:true},
  skiing:                 {cats:["outdoor","sports"],   scores:{sports:6,culture:1,tech:1,social:7,outdoor:9,creative:1,game:1},intensity:"yuru",vibe:"bright",vertical:false},
  swimming:               {cats:["sports"],             scores:{sports:8,culture:1,tech:1,social:4,outdoor:3,creative:1,game:1},intensity:"middle",vibe:"cozy",vertical:false},
  outdoor:                {cats:["outdoor"],            scores:{sports:4,culture:1,tech:1,social:8,outdoor:10,creative:1,game:1},intensity:"yuru",vibe:"bright",vertical:false},
  music:                  {cats:["culture"],            scores:{sports:1,culture:10,tech:1,social:5,outdoor:1,creative:7,game:1},intensity:"middle",vibe:"cozy",vertical:false},
  theater:                {cats:["culture","creative"], scores:{sports:1,culture:9,tech:2,social:5,outdoor:1,creative:9,game:1},intensity:"middle",vibe:"cool",vertical:false},
  cinema:                 {cats:["creative"],           scores:{sports:1,culture:6,tech:2,social:5,outdoor:1,creative:9,game:2},intensity:"yuru",vibe:"cozy",vertical:false},
  "fine-art":             {cats:["creative"],           scores:{sports:1,culture:5,tech:1,social:4,outdoor:1,creative:10,game:1},intensity:"yuru",vibe:"cozy",vertical:false},
  "international-exchange":{cats:["social"],           scores:{sports:2,culture:3,tech:2,social:10,outdoor:2,creative:2,game:1},intensity:"yuru",vibe:"bright",vertical:false},
  volunteer:              {cats:["social"],             scores:{sports:1,culture:1,tech:2,social:10,outdoor:3,creative:2,game:1},intensity:"yuru",vibe:"cozy",vertical:false},
  technology:             {cats:["tech"],               scores:{sports:1,culture:1,tech:10,social:4,outdoor:1,creative:4,game:5},intensity:"gachi",vibe:"cool",vertical:false},
  economy:                {cats:["tech"],               scores:{sports:1,culture:1,tech:9,social:5,outdoor:1,creative:3,game:1},intensity:"gachi",vibe:"cool",vertical:false},
  language:               {cats:["social"],             scores:{sports:1,culture:3,tech:3,social:9,outdoor:1,creative:2,game:1},intensity:"middle",vibe:"bright",vertical:false},
};

const UNIV_TAG_COLOR = {
  "早稲田大学":   "tag-purple",
  "法政大学":     "tag-blue",
  "東京理科大学": "tag-teal",
  "一橋大学":     "tag-gold",
  "明治大学":     "tag-pink",
  "立教大学":     "tag-purple",
  "青山学院大学": "tag-blue",
  "中央大学":     "tag-teal",
  "上智大学":     "tag-gold",
  "慶應義塾大学": "tag-pink",
  "東京大学":     "tag-gold",
};

const GACHI_KW = ["全国大会","リーグ戦優勝","大会優勝","週3","週4","週5","ガチ","本格的","競技","東京六大学"];
const YURU_KW  = ["週1","気軽","ゆるく","のんびり","自由参加","来れる時","マイペース","初心者大歓迎","初心者でも","敷居が低"];

function detectIntensity(pr, def) {
  for (const kw of GACHI_KW) if (pr.includes(kw)) return "gachi";
  for (const kw of YURU_KW)  if (pr.includes(kw)) return "yuru";
  return def;
}
function detectSize(pr) {
  if (/[1-9]\d{2,}名|100名以上|大規模/.test(pr)) return "large";
  if (/[1-5]\d名|少人数|小規模/.test(pr))         return "small";
  return "medium";
}
function makeTags(genreJa, intensity, inkare, univ) {
  const tags = [];
  tags.push({l: genreJa, c: "tag-teal"});
  if (intensity === "gachi") tags.push({l:"本気系", c:"tag-pink"});
  else if (intensity === "yuru") tags.push({l:"ゆるめ", c:"tag-gold"});
  if (inkare) tags.push({l:"インカレ", c:"tag-blue"});
  const color = UNIV_TAG_COLOR[univ] || "tag-purple";
  tags.push({l: univ, c: color});
  return tags.slice(0, 4);
}

function convertWaseda(rawList, startId = 100) {
  return rawList.map((c, i) => {
    const gkey  = c.genre_key || "outdoor";
    const ginfo = GENRE_MAP[gkey] || GENRE_MAP.outdoor;
    const pr    = c.pr_text || "";
    const catchcopy = c.catchcopy || "";
    const intensity = detectIntensity(pr, ginfo.intensity);
    const size = detectSize(pr);

    const instaMatch = pr.match(/https?:\/\/(?:www\.)?instagram\.com\/([A-Za-z0-9_.]+)\/?/);
    const snsInstagram = (instaMatch && !instaMatch[0].includes("wasedaweekly")) ? "@" + instaMatch[1] : "";
    const twMatch = pr.match(/https?:\/\/(?:www\.)?(?:twitter|x)\.com\/([A-Za-z0-9_]+)\/?/);
    const snsTwitter = (twMatch && !twMatch[0].includes("wasedaweekly")) ? "@" + twMatch[1] : "";

    let desc = "";
    if (pr && pr.length > 20) {
      const first = pr.split(/[。\n]/)[0].trim();
      if (first.length > 15) desc = first.substring(0, 120) + (first.length > 120 ? "…" : "");
    }
    if (!desc) desc = catchcopy ? catchcopy.substring(0, 120) : "詳細はリンクからご確認ください。";

    const imgUrl = c.image_url || "";
    const noImg = "waseda_no_image";
    const photoKey = (imgUrl && !imgUrl.includes(noImg)) ? imgUrl : `smc_ws${c.id}/400/400`;

    return {
      id:         startId + i,
      name:       c.name,
      university: "早稲田大学",
      inkare:     false,
      catchcopy:  catchcopy,
      desc:       desc,
      categories: ginfo.cats,
      intensity:  intensity,
      vibe:       ginfo.vibe,
      size:       size,
      cost:       "medium",
      vertical:   ginfo.vertical,
      activity:   "詳細はサイト参照",
      members:    "詳細はサイト参照",
      tags:       makeTags(c.genre_ja, intensity, false, "早稲田大学"),
      instagram:  snsInstagram || ("@" + c.name.replace(/[\s　]/g,"_").substring(0,20)),
      photos:     [photoKey, `smc_ws${c.id}b/200/200`, `smc_ws${c.id}c/200/200`],
      scores:     ginfo.scores,
      waseda_id:  c.id,
      detail_url: c.detail_url || "",
      image_url:  imgUrl,
    };
  });
}

function convertMulti(rawList, startId = 400) {
  return rawList.map((c, i) => {
    const gkey  = c.genre_key || "outdoor";
    const ginfo = GENRE_MAP[gkey] || GENRE_MAP.outdoor;
    const pr    = c.pr_text || "";
    const name  = c.name;
    const univ  = c.university;
    const intensity = detectIntensity(pr, ginfo.intensity);

    let desc = pr ? pr.substring(0, 120) + (pr.length > 120 ? "…" : "") : name;
    desc = desc.split(/[。\n]/)[0].trim().substring(0, 120);
    if (!desc) desc = name;

    const seed = `smc_${c.id}`;
    return {
      id:         startId + i,
      name:       name,
      university: univ,
      inkare:     false,
      catchcopy:  c.catchcopy || name,
      desc:       desc,
      categories: ginfo.cats,
      intensity:  intensity,
      vibe:       ginfo.vibe,
      size:       "medium",
      cost:       "medium",
      vertical:   ginfo.vertical,
      activity:   "詳細はサイト参照",
      members:    "詳細はサイト参照",
      tags:       makeTags(c.genre_ja, intensity, false, univ),
      instagram:  "",
      photos:     [`${seed}/400/400`, `${seed}b/200/200`, `${seed}c/200/200`],
      scores:     ginfo.scores,
      detail_url: c.detail_url || "",
      image_url:  "",
    };
  });
}

// --- メイン処理 ---
const wasedaRaw = JSON.parse(fs.readFileSync(SRC_WASEDA, 'utf8'));
const multiRaw  = JSON.parse(fs.readFileSync(SRC_MULTI,  'utf8'));
const pdfRaw    = JSON.parse(fs.readFileSync(SRC_PDF,    'utf8'));

const wasedaCircles = convertWaseda(wasedaRaw, 100);
const multiCircles  = convertMulti(multiRaw,   400);
const pdfCircles    = convertMulti(pdfRaw,    2000);

const allCircles = [...wasedaCircles, ...multiCircles, ...pdfCircles];
const total = allCircles.length;

const univCount = {};
allCircles.forEach(c => { univCount[c.university] = (univCount[c.university] || 0) + 1; });

const js = `// 全大学公認サークルデータ（自動生成）\n// 総件数: ${total}件\nconst ALL_CIRCLES = ${JSON.stringify(allCircles, null, 2)};\n`;
fs.writeFileSync(DEST, js, 'utf8');

console.log(`✅ ${DEST} に ${total}件 出力完了`);
console.log('\n--- 大学別件数 ---');
Object.entries(univCount).sort((a,b) => b[1]-a[1]).forEach(([u,cnt]) => console.log(`  ${u}: ${cnt}件`));
