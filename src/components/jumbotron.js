import React from "react";


const Jumbotron = (props) => {
    return ( 
        <div>
            <main class="px-3 mb-auto ">
                <h1 className="middle-title">Welcome to MutCompute</h1>
                <p className="lead">Modern solutions for protein engineering. <br /> Deep Learning guided predictions for protein mutagenesis,<br /> visualized in 3D. </p>
                <p className="lead">
                  <a href="/NN/" className="btn btn-lg btn-secondary fw-bold border-dark rounded">Predict</a>
                  <a href="/ngl" className="btn btn-lg btn-secondary fw-bold border-dark rounded">Visualize</a>
                </p>
            </main>
        </div>
    )
}

export default Jumbotron