(() => {
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "GET_PRODUCT_NAME") {
      console.log("Received GET_PRODUCT_NAME action");

      const mainDiv = document.querySelector("div.css-1v7u6og.eanm77i0 div");
      if (mainDiv) {
        console.log("Main div found:", mainDiv);
      }
      const brandElement = document.querySelector('a[data-at="brand_name"]');
      const productElement = document.querySelector('span[data-at="product_name"]');
      const brandName = brandElement ? brandElement.textContent.trim() : null;
      const productName = productElement ? productElement.textContent.trim() : null;

      console.log("Brand Element:", brandElement);
      console.log("Brand Name:", brandName);
      console.log("Product Name:", productName);

      sendResponse({ brandName: brandName, productName: productName });
    }
  });
})();
