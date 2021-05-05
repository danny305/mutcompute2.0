import React, { useState }  from 'react';


const NNPage = () => {
    const [pdbId, setPdbId] = useState(null);
    const [pdbFile, setPdbFile] = useState(null);
    const [error, setError] = useState(false)
    //const [data, setData] = useState(null)

    const submitProtein = e => {
        if (pdbFile) { 
            e.preventDefault()
            fetch('/api/nn', {
                method: 'post',
                url:'/nn', 
                body: pdbFile,
                headers: {
                    'content-type': 'application/json'
                  }
            })
            .then(r => { 
                if (r.status === 200) {
                    console.log(r)
                    alert('Success ')
                }
                else {alert('error')}
            })
        }
        else if (!pdbFile && pdbId) {
        e.preventDefault()
        fetch('/api/nn', {
            method: 'post',
            url:'/nn', 
            body: JSON.stringify(pdbId),
            headers: {
                'content-type': 'application/json'
              }
        })
        .then(r => { 
            if (r.status === 200) {
                console.log(r)
                alert('Success ')
            }
            else {alert('error')}
        })
    } else {
        alert('please fill form')
    }
    }


const handleFile = e => {
    const file = e.target.value
    //console.log(file)
    const formData = new FormData()
    formData.append('file', file)
    setPdbFile(formData)
}

const handleId = e => {
    console.log(e)
    if (e.length === 4){
        setPdbId(e.toUppercase)
        console.log('4')
    } else {
        return
    }
} 

return (
    <div className="container-fluid avoid-navbar">
        {/* <section className="container container-page"> */}
                <div className="col-sm-12 page-header">
                    <h1 className="dark-grey">Protein Crystal Structure Submission<small></small></h1>
                </div>
            <form onSubmit={submitProtein}>
                <div className='nnContainer container container-page'>
                    <div className="nnInput form-group col-sm-2">
                        <input 
                        className="form-control" 
                        placeholder="PDB ID"
                        onChange={e => handleId(e.target.value)}
                        minLength='4'
                        maxLength='4'
                        ></input>
                    </div>
                        <label className="form-label">Upload Custom/In-house PDB:</label>
                    <div className="form-group col-sm-3">
                        <input 
                        className="form-control form-control-sm" 
                        type="file" 
                        id="formFile"
                        onChange={handleFile}>    
                        </input>
                    </div>
                </div>
            {/* </form> */}
        {/* </section> */}
        <section className="container">
            <hr />
            <div className="container">
                <br />
                <div className="col-md-6 text-justify">
                    <h3 className="dark-grey"><strong>Upon Submission</strong></h3>
                    <p>
                        By clicking on "Submit" you agree to the <a href="/terms">Terms and Conditions</a>.
                    </p>
                    <p>
                        The data will be emailed to you upon completion.
                    </p>
                    <p>
                        This Protein Neural Net is still an on going research project in the Ellington Research Lab
                        and may be temporarily offline for updates and the addition of new features.
                    </p>
                    <p>
                        Please visit the <a href="/FAQ">FAQ page</a> for additional details.
                    </p>
                </div>
            </div>
            <div className="col-sm-6">
                <br />
                <button type="submit" className="w-20 btn btn-lg btn-primary">Submit</button>
            </div> 
        </section>
        </form>
    </div>
)
}

export default NNPage