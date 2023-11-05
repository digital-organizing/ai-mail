const contextElement = (context) => {
  return `
  <div class="card-body">
    <p class="card-text">${context.sentence}</p>
    <h6 class="card-subtitle mb-2 text-body-secondary">Score: ${
      context.distance
    }</h6>
    <footer>${JSON.stringify(context.meta)}</footer>
  </div>
`;
};

document
  .querySelector("#inputForm")
  .addEventListener("submit", async (event) => {
    event.preventDefault();

    const data = new FormData(event.target);

    document.querySelector("#outputArea").value = "";
    document.querySelector(".spinner-border").classList.remove("d-none");

    const response = await fetch("", {
      method: "POST",
      body: data,
    }).then((response) => response.json());

    document.querySelector("#outputArea").value = response.message;
    document.querySelector(".spinner-border").classList.add("d-none");
    const contextContainer = document.querySelector("#context");
    contextContainer.innerHTML = "";
    response.results.forEach((element) => {
      const card = document.createElement("div");
      card.classList.add("card");
      card.innerHTML = contextElement(element);
      contextContainer.appendChild(card);
    });
  });
