import { getActiveTabURL } from "./utils.js";
(() => {
const questions = [
  {
    question: "What is the primary skin concern you are hoping to address with this product?(Select One)",
    options: ["Dryness", "Dullness", "Oiliness", "Acne/blemishes", "Aging (fine lines/wrinkles, loss of firmness/elasticity)", "Hyperpigmentation/Dark Spots", "Pores", "Uneven texture", "Uneven skin tone", "Redness"],
    progress: "17%",
    step: "1/6"
  },
  {
    question: "How severe is this",
    options: ["Mild", "Medium", "Severe"],
    progress: "34%",
    step: "2/6"
  },
  {
    question: "What is your skin type?",
    options: ["Dry", "Oily", "Normal", "Combination"],
    progress: "51%",
    step: "3/6"
  },
  {
    question: "Does your skin react poorly to new products?",
    options: ["Yes", "No"],
    progress: "68%",
    step: "4/6"
  },
  {
    question: "How do you feel about fragrances?",
    options: ["Love them", "Hate them", "Don't care"],
    progress: "85%",
    step: "5/6"
  },
  {
    question: "What age range do you fall within?",
    options: ["Under 19", "19-29", "30-49", "50-59", "60+"],
    progress: "100%",
    step: "6/6"
  }
];

let currentQuestionIndex = 0;
const answers = {};

const form = document.getElementById('questions-form');
const questionLabel = form.querySelector('label');
const optionsContainer = form.querySelector('.options');
const progressBar = document.querySelector('.progress');
const progressText = document.querySelector('.progress-text');
const backButton = document.querySelector('.back');
const finishButton = document.querySelector('.finish');

function loadQuestion(index) {
  const question = questions[index];
  questionLabel.textContent = question.question;
  if (index === 1) {
    const previousAnswers = answers[questions[0].question].join(", ");
    questionLabel.textContent += ` ${previousAnswers}?`;
  }
  optionsContainer.innerHTML = question.options.map(option => `
    <label><input type="${index === 0 ? 'radio' : 'radio'}" name="option" value="${option}"><span>${option}</span></label>
  `).join('');
  progressBar.style.width = question.progress;
  progressText.textContent = question.step;

  backButton.disabled = index === 0;
  finishButton.textContent = index === questions.length - 1 ? 'FINISH' : 'NEXT';
}

backButton.addEventListener('click', function() {
  if (currentQuestionIndex > 0) {
    currentQuestionIndex--;
    loadQuestion(currentQuestionIndex);
  }
});

document.querySelector('.close-button').addEventListener('click', function() {
  window.close();
});

async function checkProduct(productName, brandName) {

  const identityToken = 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImUyNmQ5MTdiMWZlOGRlMTMzODJhYTdjYzlhMWQ2ZTkzMjYyZjMzZTIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTExNDU1MjkxNzAyOTAzODgxNTg3IiwiaGQiOiJkZXJtYXNrYW4uY29tIiwiZW1haWwiOiJ2YXNhbnRoQGRlcm1hc2thbi5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6Imo3THRsVll2ZkNjRFAzSWZFekZra1EiLCJuYmYiOjE3MjI2MjgxMjksImlhdCI6MTcyMjYyODQyOSwiZXhwIjoxNzIyNjMyMDI5LCJqdGkiOiIzY2Q3YTNlMDhjOTFiOTQ4OGRhZjc3OWNlMWMwNzM0Y2U4MTE5NzE3In0.I2-R6-G4Tufpp8Hm1VJo2Xp3Yt3QoD5i563gaoy9KchEHJk_YOKOruE0oeXoRqbEdHldhUwAOkmWpkXxrVah79OSVys0D42yfsnNAMLZHCHLX_jZ_tVkFl3QU6D6KMaKvViMBROmNG1RfUrLAhO7BEbJ6D8FjJVYgrp5gTNFSqdLLpdfyRnkjsAqQI4KrcYnB4MTZhwZ7betkNlild-KF3EpiB9YZAi7ELQC2LJHrRWU4TbRyujRe7uQmXoNTAsxX_M6grojD6_a_IgW3RJ45xDAaIClYA8Qq6qUIkQd67Wbke8COMVL2-0mikURmrjHQPMdf_VwO3TtS6jz2Dmt-g';
  const response = await fetch(`https://staging-backend-hi4mdxt3wa-uc.a.run.app/api/product/${(productName)}/${(brandName)}`, {
      method: 'GET',
      mode: 'cors',
      headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${identityToken}`
      }
  });

  if (response.ok) {
      const data = await response.json();
      if (data.product) {
          return true;
      } else {
          return false;
      }
  } else {
      console.log('Error:', response.statusText);
      return false; 
  }
}


document.addEventListener("DOMContentLoaded", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const activeTab = tabs[0];

      if (activeTab.url.includes("https://www.sephora.com/product/")) {
          chrome.tabs.sendMessage(activeTab.id, { action: "GET_PRODUCT_NAME" }, async (response) => {
              const check = await checkProduct(response.productName, response.brandName);
              if (check) {
                  loadQuestion(currentQuestionIndex);
                  setupFormSubmission(response.productName, response.brandName);
              } else {
                  const container = document.getElementsByClassName("container")[0];
                  container.innerHTML = `
                      <div style="
                          width: 500px;
                          height: 500px;
                          padding: 0px;
                          background-color: #fff;
                          display: flex;
                          flex-direction: column;
                          align-items: center;
                          justify-content: center;
                          position: relative;
                          overflow: hidden;
                        ">
                        <div class="logo">
                            <img src="assets/main.png" alt="Logo">
                            <div class="bookmarks" id="bookmarks"></div>
                          </div>
                          <div class="title">We are still working on these products. They will be added soon. Thank you!</div>
                      `;
              }
          });
      } else {
          const container = document.getElementsByClassName("container")[0];
          container.innerHTML = `
          <div style="
              width: 500px;
              height: 500px;
              padding: 0px;
              background-color: #fff;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              position: relative;
              overflow: hidden;
            ">
            <div class="logo">
                <img src="assets/main.png" alt="Logo">
                <div class="bookmarks" id="bookmarks"></div>
              </div>
              <div class="title">This is not a Sephora product page.</div>'
          `;

      }
  });
});
function setupFormSubmission(productName, brandName) {
  form.addEventListener('submit', function(event) {
    event.preventDefault();

    const selectedOptions = Array.from(form.querySelectorAll('input[name="option"]:checked'));

    if (selectedOptions.length === 0) {
      alert('Please select an option.');
      return;
    }

    const questionText = questions[currentQuestionIndex].question;
    answers[questionText] = selectedOptions.map(option => option.value);

    if (currentQuestionIndex < questions.length - 1) {
      currentQuestionIndex++;
      loadQuestion(currentQuestionIndex);
    } else {
      const dataToSend = {
        answers: answers,
        product_name: productName,
        brand_name: brandName
      };
      console.log(dataToSend);

      const identityToken = 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImUyNmQ5MTdiMWZlOGRlMTMzODJhYTdjYzlhMWQ2ZTkzMjYyZjMzZTIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJhY2NvdW50cy5nb29nbGUuY29tIiwiYXpwIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiNjE4MTA0NzA4MDU0LTlyOXMxYzRhbGczNmVybGl1Y2hvOXQ1Mm4zMm42ZGdxLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTExNDU1MjkxNzAyOTAzODgxNTg3IiwiaGQiOiJkZXJtYXNrYW4uY29tIiwiZW1haWwiOiJ2YXNhbnRoQGRlcm1hc2thbi5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6Imo3THRsVll2ZkNjRFAzSWZFekZra1EiLCJuYmYiOjE3MjI2MjgxMjksImlhdCI6MTcyMjYyODQyOSwiZXhwIjoxNzIyNjMyMDI5LCJqdGkiOiIzY2Q3YTNlMDhjOTFiOTQ4OGRhZjc3OWNlMWMwNzM0Y2U4MTE5NzE3In0.I2-R6-G4Tufpp8Hm1VJo2Xp3Yt3QoD5i563gaoy9KchEHJk_YOKOruE0oeXoRqbEdHldhUwAOkmWpkXxrVah79OSVys0D42yfsnNAMLZHCHLX_jZ_tVkFl3QU6D6KMaKvViMBROmNG1RfUrLAhO7BEbJ6D8FjJVYgrp5gTNFSqdLLpdfyRnkjsAqQI4KrcYnB4MTZhwZ7betkNlild-KF3EpiB9YZAi7ELQC2LJHrRWU4TbRyujRe7uQmXoNTAsxX_M6grojD6_a_IgW3RJ45xDAaIClYA8Qq6qUIkQd67Wbke8COMVL2-0mikURmrjHQPMdf_VwO3TtS6jz2Dmt-g';
      const loadingHtml = `
      <div style="
          width: 500px;
          height: 500px;
          padding: 0;
          background-color: #fff;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
      ">
          <div class="logo">
              <img src="assets/main.png" alt="Logo">
              <div class="bookmarks" id="bookmarks"></div>
          </div>
          <p>DermaSkan analyzing product ingredients</p>
          <div class="loading-spinner"></div>
      </div>
      `;

      document.querySelector('.container').innerHTML = loadingHtml;

      const spinnerDiv = document.querySelector('.loading-spinner');

      spinnerDiv.style.width = '40px';
      spinnerDiv.style.height = '40px';
      spinnerDiv.style.border = '4px solid #f3f3f3';
      spinnerDiv.style.borderTop = '4px solid #f57c00'; 
      spinnerDiv.style.borderRadius = '50%';
      spinnerDiv.style.animation = 'spin 1s linear infinite';
      spinnerDiv.style.marginTop = '20px';


      const style = document.createElement('style');
      style.textContent = `
      @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
      }
      `;

      document.head.appendChild(style);


      fetch('https://staging-backend-hi4mdxt3wa-uc.a.run.app/api/survey', {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${identityToken}`
        },
        body: JSON.stringify(dataToSend)
      })
      .then(response => response.json())
      .then(data => {
        console.log('Survey completed:', data);
        const resultValue = data.results;
        const map_results = ['Not Recommended','OK','Great','Excellent']
        const resultLabels = ['This product is not recommended for you', 'This product might be ok, but there are better options out there', 'This product is a well suited to give you the desired results', 'This product is perfectly suited to give you the desired results'];
        const resultLabel = resultLabels[resultValue];
        const result = map_results[resultValue];
        const exp = data.statement;
        const container = document.querySelector('.container');
        let meterValue;
          switch (result) {
            case 'Not Recommended':
              meterValue = 0;
              break;
            case 'OK':
              meterValue = 1;
              break;
            case 'Great':
              meterValue = 2;
              break;
            case 'Excellent':
              meterValue = 3;
              break;
            default:
              meterValue = 0;
          }   
          const loadingHtml = `
          <div style="
            width: 500px;
            height: 500px;
            padding: 0;
            background-color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
          ">
          <div class="logo">
              <img src="assets/main.png" alt="Logo">
              <div class="bookmarks" id="bookmarks"></div>
          </div>
          <button class="close-button">&times;</button>
          <div style="font-size: 24px; font-weight: bold; text-align: center; margin-top: 10px; margin-bottom: 10px;">
              YOUR RESULT
          </div>
          <canvas id="myPieChart" width="300" height="150"></canvas>
          <div id="explanation"></div>
          </div>
        `
        container.innerHTML = loadingHtml;
        var canvas = document.getElementById('myPieChart');
        canvas.height = canvas.width / 2;
        var ctx = canvas.getContext('2d');
        var angles = [180 * 0.25, 180 * 0.25, 180 * 0.25, 180 * 0.25];
        var labels = ['Not Recommended', 'OK', 'Great', 'Excellent'];
        var highlightLabel = result;
        var startAngle = Math.PI;
        var radius = 150;
        var centerX = canvas.width / 2;
        var centerY = canvas.height;
        var cumulativeAngle = startAngle;
        angles.forEach(function(angle, index) {
          var endAngle = cumulativeAngle + angle * Math.PI / 180;
          var midAngle = cumulativeAngle + (angle / 2) * Math.PI / 180; 
          ctx.fillStyle = labels[index] === highlightLabel ? '#000000' : '#D3D3D3';
          ctx.beginPath();
          ctx.moveTo(centerX, centerY); 
          ctx.arc(centerX, centerY, radius, cumulativeAngle, endAngle);
          ctx.lineTo(centerX, centerY);
          ctx.fill();
          ctx.beginPath();
          ctx.strokeStyle = '#FFFFFF';
          ctx.lineWidth = 2;
          ctx.moveTo(centerX, centerY);
          ctx.lineTo(centerX + radius * Math.cos(cumulativeAngle), centerY + radius * Math.sin(cumulativeAngle));
          ctx.stroke();
          ctx.fillStyle = labels[index] === highlightLabel ? '#FFFFFF' : '#000000'; 
          ctx.font = 'bold 14px Arial'; 
          ctx.textAlign = 'center';
          var labelRadius = radius * 0.62; 
          var labelX = centerX + labelRadius * Math.cos(midAngle);
          var labelY = centerY + labelRadius * Math.sin(midAngle);
      
          if (labels[index] === 'Not Recommended') {
              ctx.fillText('Not', labelX, labelY - 7);
              ctx.fillText('Recommended', labelX, labelY + 10);
          } else {
              ctx.fillText(labels[index], labelX, labelY + 6);
          }
          cumulativeAngle = endAngle;
      });
      ctx.beginPath();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2;
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(centerX + radius * Math.cos(cumulativeAngle), centerY + radius * Math.sin(cumulativeAngle));
      ctx.stroke();
      document.getElementById('explanation').style.textAlign = 'center';
      document.getElementById('explanation').style.padding = '20px';
      document.getElementById('explanation').innerText = exp;
      document.querySelector('.close-button').style.cssText = 'position: absolute; top: 24px; right: 24px; background: none; border: none; font-size: 21.6px; cursor: pointer;';
        document.querySelector('.close-button').addEventListener('click', function() {
          window.close();
        });    
      });
    }
  });
}
})();