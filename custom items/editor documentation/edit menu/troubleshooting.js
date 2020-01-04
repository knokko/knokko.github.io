function processConsoleDump(){
    const dumpArea = document.getElementById("console-dump");
    const log = dumpArea.value;
    const output = document.getElementById("check-output");

    output.innerText = findError(log);
}

function findError(log){
    if (log.length === 0) {
        return "You need to paste the console log in the box above before clicking on this.";
    }

    if (log.includes("Editor")) {
        return "It looks like you put the editor in the plugins folder. Please don't do that.";
    }

    if (!log.includes("CustomItems")) {
        return "The console log doesn't contain 'CustomItems'. Is it really in the plugins folder?";
    }

    if (!log.includes("KnokkoCore")) {
        return "The console log doesn't contain 'KnokkoCore'. Is it really in the plugins folder?";
    }

    if (log.includes("No custom item set could be found in the Custom Items plugin data folder")) {
        return `It looks like the plug-in couldn't find a file ending with '.cis' or '.txt'. 
        Are you sure there is such a file in ServerFolder/plugins/CustomItems? 
        And did you restart your server?`;
    }

    if (log.includes("Multiple custom item sets were found")) {
        return `More than 1 item set was found in your CustomItems folder. It could be that you put both
        the .cis file and .txt file in the CustomItems folder. Please don't. Doing so is unneccessary and
        you might keep using the old item set if you forget to replace one of them upon uploading a newer
        version of your item set. If you want to use 2 different item sets, at the same time, you need to
        look into COMBINING them via the Editor.`;
    }

    if (log.includes("Unknown encoding")) {
        return `It looks like the CustomItems version you are using is older than the editor you used.
        Please install the latest version of CustomItems, remove your current version and restart your server.`;
    }

    if (log.includes("NoSuchMethodError: nl.knokko") || log.includes("NoClassDefFoundError: nl/knokko/")) {
        return "It looks like your Knokko Core is outdated, please install a newer version.";
    }

    if (log.includes("nl.knokko")) {
        const firstIndex = log.indexOf("nl.knokko");
        const startIndex = Math.max(0, firstIndex - 3000);
        const endIndex = Math.min(log.length - 1, firstIndex + 4000);
        return `It looks like you're in the rare case where the mistake is mine.
        Please post (part of) the following part on the discord or BukkitDev:

        ${log.substring(startIndex, endIndex)}`;
    }

    return "No problems in your console log were found, this will really require manual attention...";
}