// 送出防手震:1 秒內的重複 queuePrompt 直接忽略
// 避免連點 Run / 按鍵重複 / 快捷鍵與按鈕同時觸發時,
// 同一個任務被送出兩次(Replicate API 會重複扣費)
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ReplicateAPI_NM.QueueGuard",
    setup() {
        const original = app.queuePrompt.bind(app);
        let lastQueuedAt = 0;
        const WINDOW_MS = 1000;

        app.queuePrompt = async function (...args) {
            const now = Date.now();
            if (now - lastQueuedAt < WINDOW_MS) {
                console.warn(`[Replicate API NM] 忽略 ${WINDOW_MS}ms 內的重複送出 / duplicate queue ignored`);
                return;
            }
            lastQueuedAt = now;
            return original(...args);
        };
    },
});
