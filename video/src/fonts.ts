import { loadFont as loadNoto } from "@remotion/google-fonts/NotoSans";
import { loadFont as loadRoboto } from "@remotion/google-fonts/Roboto";

export const { fontFamily: SANS } = loadNoto("normal", { weights: ["400", "500", "700", "800", "900"], subsets: ["latin"] });
export const { fontFamily: NUM } = loadRoboto("normal", { weights: ["500", "700", "900"], subsets: ["latin"] });
