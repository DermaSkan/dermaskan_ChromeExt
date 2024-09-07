chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.url && tab.url.includes("sephora.com/") && changeInfo.status === 'complete') {
    chrome.tabs.sendMessage(tabId, { action: "GET_PRODUCT_NAME" }, (response) => {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError);
      } else {
        console.log('Response from content script:', response);
      }
    });
  }

});
