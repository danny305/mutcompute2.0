import React, { useEffect } from 'react';
import * as NGL from 'ngl';
import { withRouter } from "react-router";
import useFile from '../hooks/useFile';
import { useHistory } from 'react-router-dom'


const Compvis3 = (props) => {

const pdbIdUrl = props.match.params.id || props.id

const { fetchFile }= useFile()

const history = useHistory()

    useEffect (() => {

      const handleFile = (dataObj) => {
        if (dataObj.error) {
          const noValue = Object.values(dataObj)
          const emptyBlob = new Blob([noValue], {type: 'text/plain'})
          alert('Please log in to view predictions')
          loadStructure(`rcsb://${pdbIdUrl}.pdb`, emptyBlob)
        } else if (!dataObj.predictions){
          alert('Predictions unavailable. Please run protein through neural net before visualizing')
          history.push('/nn')
        } else {
        var csvBlob = new Blob( [ dataObj.predictions ], {type: 'text/plain'})
        console.log(csvBlob)
        loadStructure(`rcsb://${pdbIdUrl}.pdb`, csvBlob)
        }
      }

      fetchFile(pdbIdUrl, handleFile)

      const stage = new NGL.Stage( "viewport" );
      window.addEventListener( "resize", function( event ){
          stage.handleResize();
      }, false );

      // Change background color for Hong
        // stage.setParameters({
        //   backgroundColor: 'white'
        // })

    function addElement (el) {
        Object.assign(el.style, {
          position: 'absolute',
          zIndex: 10
        })
        stage.viewer.container.appendChild(el)
      }

      function createElement (name, properties, style) {
        var el = document.createElement(name)
        Object.assign(el, properties)
        Object.assign(el.style, style)
        return el
      }

      function createSelect (options, properties, style) {
        var select = createElement('select', properties, style)
        options.forEach(function (d) {
          select.add(createElement('option', {
            value: d[0], text: d[1]
          }))
        })
        return select
      }

      // FUTURE FEATURE
      // function createFileButton (label, properties, style) {
      //   var input = createElement('input', Object.assign({
      //     type: 'file'
      //   }, properties), { display: 'none' })
      //   addElement(input)
      //   var button = createElement('input', {
      //     value: label,
      //     type: 'button',
      //     onclick: function () { input.click() }
      //   }, style)
      //   return button
      // }

      var topPosition = 75

      function getTopPosition (increment) {
        if (increment) topPosition += increment
        return topPosition + 'px'
      }
  
      var tooltip = document.createElement('div')
      Object.assign(tooltip.style, {
        display: 'none',
        position: 'fixed',
        zIndex: 10,
        pointerEvents: 'none',
        backgroundColor: 'rgba( 0, 0, 0, 0.6 )',
        color: 'lightgrey',
        padding: '8px',
        fontFamily: 'sans-serif'
      })
      document.body.appendChild(tooltip)

      // remove default hoverPick mouse action
      stage.mouseControls.remove('hoverPick')
      // listen to `hovered` signal to move tooltip around and change its text
      stage.signals.hovered.add(function (pickingProxy) {
        if (cartoonCheckbox.checked === true || customCheckbox.checked === true) {
          if (pickingProxy && (pickingProxy.atom || pickingProxy.bond)) {
            var atom = pickingProxy.atom || pickingProxy.closestBondAtom
            const csvRow = residueData[atom.resno]
            if (csvRow !== undefined) {
              const wtProb = parseFloat(csvRow[csvWtProbCol])
              const prProb = parseFloat(csvRow[csvPrProbCol])
              const foldChange = parseFloat(csvRow[csvFoldChange])
              tooltip.innerHTML = `
            CHAIN: ${atom.chainname}<br/>
            RES NUM: ${atom.resno}<br/>
            WT AA: ${atom.resname}<br/>
            WT PROB: ${wtProb.toFixed(4)}<br/>
            PRED AA: ${csvRow[csvPrAaCol]}<br/>
            PRED PROB: ${prProb.toFixed(4)}<br/>
            LOG2 PRED/WT: ${foldChange.toFixed(4)}`
            // LOG2 PRED/WT: ${Math.log2(prProb/wtProb).toFixed(3)}`
              tooltip.style.bottom = stage.viewer.height - 170 + 'px'
              tooltip.style.left = stage.viewer.width - 190 + 'px'
              tooltip.style.display = 'block'
            } else {
              tooltip.style.display = 'none'
            }
          }
        }
      })


      var ligandSele = '( not polymer or not ( protein or nucleic ) ) and not ( water or ACE or NH2 )'

      var pocketRadius = 0
      var pocketRadiusClipFactor = 1

      var cartoonRepr, neighborRepr, ligandRepr, waterRepr, contactRepr, pocketRepr, labelRepr, customRepr

      var struc
      var csv
      var residueData

      var heatMap
      var customPercent

      var neighborSele
      var sidechainAttached = false

      // FUTURE FEATURE
      //var loadStrucFile, loadCsvFile

      // NEW FILES
      // const csvResNumCol = 4
      // const csvWtProbCol = 7
      // const csvPrAaCol = 6
      // const csvPrProbCol = 8

      // OLD DB FILES
      const csvResNumCol = 3
      const csvWtProbCol = 6
      const csvPrAaCol = 5
      const csvPrProbCol = 7
      const csvFoldChange = 8

      function loadStructure (proteinFile, csvFile) {
        struc = undefined
        stage.setFocus(0)
        stage.removeAllComponents()
        ligandSelect.innerHTML = ''
        clipNearRange.value = 0
        clipRadiusRange.value = 100
        pocketOpacityRange.value = 30
        cartoonCheckbox.checked = true
        customCheckbox.checked = false
        sidechainAttachedCheckbox.checked = false
        waterIonCheckbox.checked = false
        hydrophobicCheckbox.checked = false
        hydrogenBondCheckbox.checked = false
        weakHydrogenBondCheckbox.checked = false
        waterHydrogenBondCheckbox.checked = false
        backboneHydrogenBondCheckbox.checked = false
        halogenBondCheckbox.checked = true
        metalInteractionCheckbox.checked = true
        saltBridgeCheckbox.checked = true
        cationPiCheckbox.checked = true
        piStackingCheckbox.checked = true
        return Promise.all([
          stage.loadFile(proteinFile /*, { defaultRepresentation: true } <this renders 1 biological unit>*/),
          NGL.autoLoad(csvFile, {
            ext: 'csv',
            delimiter: ',',
            comment: '#',
            columnNames: true
          })
        ]).then(function (ol) {
          struc = ol[0]
          csv = ol[1].data
        
          setLigandOptions()
          setChainOptions()
          setResidueOptions()
        
          residueData = {}
          for (var i = 0; i < csv.length; i++) {
            const resNum = parseFloat(csv[i][csvResNumCol])
            residueData[resNum] = csv[i]
          }
      
          heatMap = NGL.ColormakerRegistry.addScheme(function (params) {
            this.parameters = Object.assign(this.parameters, {
              domain: [0, 0.30],
              scale: 'rwb',
              // Hong custom color scale
              //scale: [0xFF0000,0xFFFFFF,0x4646FF],
              mode: 'rgb'
            })
            var scale = this.getScale()
            this.atomColor = function (atom) {
              const csvRow = residueData[atom.resno]
              if (atom.isNucleic()) {
                return 0x004e00
              }
              if (csvRow !== undefined) {
                const wtProb = parseFloat(csvRow[csvWtProbCol])
                return scale(wtProb)
              } else {
                return 0xcccccc
              }
            }
          })
      
          customPercent = NGL.ColormakerRegistry.addScheme(function (params) {
            this.atomColor = function (atom) {
              for (var i = 0; i < csv.length; i++) {
                const csvRow = residueData[atom.resno]
            
                if (atom.isNucleic()) {
                  return 0x004e00
                }
                if (csvRow !== undefined) {
                  const wtProb = parseFloat(csvRow[csvWtProbCol])
                  //const predProb = parseFloat(csvRow[csvPrProbCol])
                  if (wtProb < 0.01 ) {
                    return 0xF800080// purple
                  } else if (wtProb < 0.03) {
                    return 0xFF0000 // red
                  } else if (wtProb < 0.05) {
                    return 0xFFA500 // orange
                  } else if (wtProb < 0.10) {
                    return 0xFFFF00 // yellow 
                  } else {
                    return 0xFFFFFF // white
                  }
                }
              }
            }
          })
      
          struc.autoView()
          cartoonRepr = struc.addRepresentation('cartoon', {
            color: heatMap,
            visible: true
          })
          customRepr = struc.addRepresentation('cartoon', {
            color: customPercent,
            visible: false
          })
          neighborRepr = struc.addRepresentation('ball+stick', {
            sele: 'none',
            aspectRatio: 1.1,
            colorValue: 'lightgrey',
            multipleBond: 'symmetric',
            //changed opacity for Hong
            opacity: 0.7
          })
          ligandRepr = struc.addRepresentation('ball+stick', {
            multipleBond: 'symmetric',
            colorValue: 'grey',
            sele: 'none',
            aspectRatio: 1.2,
            radiusScale: 2.5
          })
          waterRepr = struc.addRepresentation('ball+stick', {
            name: 'waterIon',
            visible: waterIonCheckbox.checked,
            sele: 'water or ion',
            aspectRatio: 1.1,
          })
          contactRepr = struc.addRepresentation('contact', {
            sele: 'none',
            radiusSize: 0.07,
            weakHydrogenBond: false,
            waterHydrogenBond: false,
            backboneHydrogenBond: false,
            hydrogenBond: false
          })
          pocketRepr = struc.addRepresentation('surface', {
            sele: 'none',
            lazy: true,
            visibility: true,
            clipNear: 0,
            opaqueBack: false,
            opacity: 0.3,
            //clipRadius: 0.1,
            color: heatMap,
            roughness: 1.0,
            surfaceType: 'av'
          })
          labelRepr = struc.addRepresentation('label', {
            sele: 'none',
            color: '#111111',
            yOffset: 0.2,
            zOffset: 2.0,
            attachment: 'bottom-center',
            showBorder: true,
            borderColor: 'lightgrey',
            borderWidth: 0.5,
            disablePicking: true,
            radiusType: 'size',
            radiusSize: 1.5,
            labelType: 'residue',
            labelGrouping: 'residue'
          })
        })
        .catch(failure)
      }

      // ERROR HANDLING -- specifically for mutcompute version (including above catch)
      function failure (error) {
        console.error(error)
        if (window.confirm('Sorry, this data does not exist. Please run your desired protein through the neural net first.')) {
          //window.location.href = 'https://mutcompute.com';
        }
      }

      function setLigandOptions () {
        ligandSelect.innerHTML = ''
        var options = [['', 'select ligand']]
        struc.structure.eachResidue(function (rp) {
          if (rp.isWater()) return
          var sele = ''
          if (rp.resno !== undefined) sele += rp.resno
          if (rp.inscode) sele += '^' + rp.inscode
          if (rp.chain) sele += ':' + rp.chainname
          var name = (rp.resname ? '[' + rp.resname + ']' : '') + sele
          if (rp.entity && rp.entity.description) name += ' (' + rp.entity.description + ')'
          options.push([sele, name])
        }, new NGL.Selection(ligandSele))
        options.forEach(function (d) {
          ligandSelect.add(createElement('option', {
            value: d[0], text: d[1]
          }))
        })
      }

      function setChainOptions () {
        chainSelect.innerHTML = ''
        var options = [['', 'select chain']]
        struc.structure.eachChain(function (cp) {
          var name = cp.chainname
          if (cp.entity && cp.entity.description) name += ' (' + cp.entity.description + ')'
          options.push([cp.chainname, name])
        }, new NGL.Selection('polymer'))
        options.forEach(function (d) {
          chainSelect.add(createElement('option', {
            value: d[0], text: d[1]
          }))
        })
      }

      function setResidueOptions (chain) {
        residueSelect.innerHTML = ''
        var options = [['', 'select residue']]
        if (chain) {
          struc.structure.eachResidue(function (rp) {
            var sele = ''
            if (rp.resno !== undefined) sele += rp.resno
            if (rp.inscode) sele += '^' + rp.inscode
            if (rp.chain) sele += ':' + rp.chainname
            var name = (rp.resname ? '[' + rp.resname + ']' : '') + sele
            options.push([sele, name])
          }, new NGL.Selection('polymer and :' + chain))
        }
        options.forEach(function (d) {
          residueSelect.add(createElement('option', {
            value: d[0], text: d[1]
          }))
        })
      } 

      // TODO Future feature to filter and search for proteins.
      // var loadStructureButton = createFileButton('Load Structure', {
      //   accept: '.pdb,.cif,.ent,.gz,.mol2',
      //   onchange: function (e) {
      //     if (e.target.files[0]) {
      //       loadStrucFile = e.target.files[0]
      //     }
      //     if (loadCsvFile) {
      //       loadStructure(loadStrucFile, loadCsvFile)
      //       loadCsvFile = ''
      //       loadStrucFile = ''
      //     }
      //   }
      // }, { top: getTopPosition(), left: '12px' })
      // addElement(loadStructureButton)   

      // var loadCsvButton = createFileButton('Load csv', {
      //   accept: '.csv',
      //   onchange: function (e) {
      //     if (e.target.files[0]) {
      //       loadCsvFile = e.target.files[0]
      //     }
      //     if (loadStrucFile) {
      //       loadStructure(loadStrucFile, loadCsvFile)
      //       loadCsvFile = ''
      //       loadStrucFile = ''
      //     }
      //   }
      // }, { top: getTopPosition(30), left: '12px' })
      // addElement(loadCsvButton) 

      // More useful for mutcompute
      // var loadPdbidInput = createElement('input', {
      //   type: 'text',
      //   placeholder: 'Enter pdbID',
      //   onkeypress: function (e) {
      //     if (e.keyCode === 13) {
      //       var inputValue = e.target.value.toLowerCase()
      //       // str.slice(0, 4)
      //       // var proteinInput = '/data/' + inputValue + '.pdb'
      //       // var csvInput = '/data/' + inputValue + '.csv'
      //       e.preventDefault(() => {
      //         history.push(`/viewer/${inputValue}`)
      //       })
      //       // loadStructure(proteinInput, csvInput)
      //       //fetchFile(inputValue, handleFile)
            
      //     }
      //   }
      // }, { top: getTopPosition(30), left: '12px', width: '120px' })
      // addElement(loadPdbidInput)    

      function showFull () {
        ligandSelect.value = '' 

        ligandRepr.setVisibility(false)
        neighborRepr.setVisibility(false)
        contactRepr.setVisibility(false)
        pocketRepr.setVisibility(false)
        labelRepr.setVisibility(false)  

        struc.autoView(2000)
      } 

      function showLigand (sele) {
        var s = struc.structure 

        // Hong -- changes b+s radius , 9 => 30+
        var withinSele = s.getAtomSetWithinSelection(new NGL.Selection(sele), 17)
        var withinGroup = s.getAtomSetWithinGroup(withinSele)
        var expandedSele = withinGroup.toSeleString()
        neighborSele = '(' + expandedSele + ') and not (' + sele + ')'
        neighborSele = expandedSele 

        var sview = s.getView(new NGL.Selection(sele))
        // Hong -- changes surface repr 100 for full struc
        pocketRadius = Math.max(sview.boundingBox.getSize(new NGL.Vector3()).length(), 2) + 15
        var withinSele2 = s.getAtomSetWithinSelection(new NGL.Selection(sele), pocketRadius + 2)
        var neighborSele2 = '(' + withinSele2.toSeleString() + ') and not (' + sele + ') and polymer'   

        ligandRepr.setVisibility(true)
        neighborRepr.setVisibility(true)
        contactRepr.setVisibility(true)
        pocketRepr.setVisibility(true)
        labelRepr.setVisibility(false)  

        ligandRepr.setSelection(sele)
        //and not (water or ion) <removes water/ions> 
        neighborRepr.setSelection(
          !sidechainAttached ? '(' + neighborSele + ') and (sidechainAttached or not polymer) and not (water or ion)' : neighborSele
        )
        waterRepr.setSelection(expandedSele)
        contactRepr.setSelection(expandedSele)
        pocketRepr.setSelection(neighborSele2)
        pocketRepr.setParameters({
          clipRadius: pocketRadius * pocketRadiusClipFactor,
          clipCenter: sview.center
        })
        //ignores water or ion for pocket coloring
        labelRepr.setSelection('(' + neighborSele + ') and not (water or ion)') 

        struc.autoView(expandedSele, 2000)
      } 

      function showRegion (sele) {
        var s = struc.structure
        ligandSelect.value = '' 

        var withinSele = s.getAtomSetWithinSelection(new NGL.Selection(sele), 5)
        var withinGroup = s.getAtomSetWithinGroup(withinSele)
        var expandedSele = withinGroup.toSeleString()
        neighborSele = '(' + expandedSele + ') and not (' + sele + ')'
        neighborSele = expandedSele 

        ligandRepr.setVisibility(false)
        neighborRepr.setVisibility(false)
        contactRepr.setVisibility(false)
        pocketRepr.setVisibility(false)
        labelRepr.setVisibility(false)  

        struc.autoView(expandedSele, 2000)
      } 

      var ligandSelect = createSelect([], {
        onchange: function (e) {
          residueSelect.value = ''
          var sele = e.target.value
          if (!sele) {
            showFull()
          } else {
            showLigand(sele)
          }
        }
      }, { top: getTopPosition(35), left: '12px', width: '130px' })
      addElement(ligandSelect)  

      var chainSelect = createSelect([], {
        onchange: function (e) {
          ligandSelect.value = ''
          residueSelect.value = ''
          setResidueOptions(e.target.value)
        }
      }, { top: getTopPosition(25), left: '12px', width: '130px' })
      addElement(chainSelect)   

      var residueSelect = createSelect([], {
        onchange: function (e) {
          ligandSelect.value = ''
          var sele = e.target.value
          if (!sele) {
            showFull()
          } else {
            showLigand(sele)
          }
        }
      }, { top: getTopPosition(25), left: '12px', width: '130px' })
      addElement(residueSelect) 

      // remove default clicking
      stage.mouseControls.remove('clickPick-left')  
      // onclick residue select and show ligandrepr
      let prevSele = ''
      stage.signals.clicked.add(function (pickingProxy) {
        let sele = ''
        if (pickingProxy && !pickingProxy.bond) {
          if (pickingProxy.atom) {
            sele += (pickingProxy.closestBondAtom || pickingProxy.atom.resno) + ':' + ((pickingProxy.closestBondAtom || pickingProxy.atom.chainname))
          }
        } 
        if (sele && sele !== prevSele) {
          showLigand(sele)
          prevSele = sele
          residueSelect.value = ''
        } else if (prevSele === sele) {
          showRegion(sele)
          prevSele = ''
          residueSelect.value = ''
        } else {
          sele = ''
          prevSele = ''
          showFull()
        }
        
      })      


      addElement(createElement('span', {
        innerText: 'pocket near clipping'
      }, { top: getTopPosition(30), left: '12px', color: 'grey' }))
      var clipNearRange = createElement('input', {
        type: 'range', value: 0, min: 0, max: 10000, step: 1
      }, { top: getTopPosition(16), left: '12px' })
      clipNearRange.oninput = function (e) {
        var sceneRadius = stage.viewer.boundingBox.getSize(new NGL.Vector3()).length() / 2  

        var f = pocketRadius / sceneRadius
        var v = parseFloat(e.target.value) / 10000 // must be between 0 and 1
        var c = 0.5 - f / 2 + v * f 

        pocketRepr.setParameters({
          clipNear: c * 100 // must be between 0 and 100
        })
      }
      addElement(clipNearRange) 

      addElement(createElement('span', {
        innerText: 'pocket radius clipping'
      }, { top: getTopPosition(25), left: '12px', color: 'grey' }))
      var clipRadiusRange = createElement('input', {
        type: 'range', value: 100, min: 1, max: 100, step: 1
      }, { top: getTopPosition(20), left: '12px' })
      clipRadiusRange.oninput = function (e) {
        pocketRadiusClipFactor = parseFloat(e.target.value) / 100
        pocketRepr.setParameters({ clipRadius: pocketRadius * pocketRadiusClipFactor })
      }
      addElement(clipRadiusRange)   

      addElement(createElement('span', {
        innerText: 'pocket opacity'
      }, { top: getTopPosition(25), left: '12px', color: 'grey' }))
      var pocketOpacityRange = createElement('input', {
        type: 'range', value: 30, min: 0, max: 100, step: 1
      }, { top: getTopPosition(20), left: '12px' })
      pocketOpacityRange.oninput = function (e) {
        pocketRepr.setParameters({
          opacity: parseFloat(e.target.value) / 100
        })
      }
      addElement(pocketOpacityRange)    

      var cartoonCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          cartoonRepr.setVisibility(e.target.checked)
        }
      }, { top: getTopPosition(30), left: '12px' })
      addElement(cartoonCheckbox)
      addElement(createElement('span', {
        innerText: 'Heat Map'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var customCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          customRepr.setVisibility(e.target.checked)
          e.target.checked? pocketRepr.setParameters({color: customPercent}) : pocketRepr.setParameters({color: heatMap})
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(customCheckbox)
      addElement(createElement('span', {
        innerText: 'Custom'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var sidechainAttachedCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          sidechainAttached = e.target.checked
          neighborRepr.setSelection(
            !sidechainAttached ? '(' + neighborSele + ') and (sidechainAttached or not polymer)' : neighborSele
          )
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(sidechainAttachedCheckbox)
      addElement(createElement('span', {
        innerText: 'sidechain'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var waterIonCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          stage.getRepresentationsByName('waterIon')
          .setVisibility(e.target.checked)
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(waterIonCheckbox)
      addElement(createElement('span', {
        innerText: 'Water Ion'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))

      var labelCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          labelRepr.setVisibility(e.target.checked)
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(labelCheckbox)
      addElement(createElement('span', {
        innerText: 'label'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var hydrophobicCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          contactRepr.setParameters({ hydrophobic: e.target.checked })
        }
      }, { top: getTopPosition(30), left: '12px' })
      addElement(hydrophobicCheckbox)
      addElement(createElement('span', {
        innerText: 'hydrophobic'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var hydrogenBondCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ hydrogenBond: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(hydrogenBondCheckbox)
      addElement(createElement('span', {
        innerText: 'hbond'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var weakHydrogenBondCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          contactRepr.setParameters({ weakHydrogenBond: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(weakHydrogenBondCheckbox)
      addElement(createElement('span', {
        innerText: 'weak hbond'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var waterHydrogenBondCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          contactRepr.setParameters({ waterHydrogenBond: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(waterHydrogenBondCheckbox)
      addElement(createElement('span', {
        innerText: 'water-water hbond'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var backboneHydrogenBondCheckbox = createElement('input', {
        type: 'checkbox',
        checked: false,
        onchange: function (e) {
          contactRepr.setParameters({ backboneHydrogenBond: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(backboneHydrogenBondCheckbox)
      addElement(createElement('span', {
        innerText: 'backbone-backbone hbond'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var halogenBondCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ halogenBond: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(halogenBondCheckbox)
      addElement(createElement('span', {
        innerText: 'halogen bond'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var metalInteractionCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ metalComplex: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(metalInteractionCheckbox)
      addElement(createElement('span', {
        innerText: 'metal interaction'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var saltBridgeCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ saltBridge: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(saltBridgeCheckbox)
      addElement(createElement('span', {
        innerText: 'salt bridge'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var cationPiCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ cationPi: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(cationPiCheckbox)
      addElement(createElement('span', {
        innerText: 'cation-pi'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      var piStackingCheckbox = createElement('input', {
        type: 'checkbox',
        checked: true,
        onchange: function (e) {
          contactRepr.setParameters({ piStacking: e.target.checked })
        }
      }, { top: getTopPosition(20), left: '12px' })
      addElement(piStackingCheckbox)
      addElement(createElement('span', {
        innerText: 'pi-stacking'
      }, { top: getTopPosition(), left: '32px', color: 'grey' }))   

      // loadStructure('/data/6ij6.pdb', '/data/6ij6.csv')
      

      }, [fetchFile, history, pdbIdUrl]);

  return (
    <div className="yes-scroll" id="viewport" style={{height: '90vh', width: '100%'}} >
      </div>
  )
}

export default withRouter(Compvis3)
  
  