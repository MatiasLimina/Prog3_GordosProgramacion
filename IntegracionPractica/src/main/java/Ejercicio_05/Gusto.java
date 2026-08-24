package Ejercicio_05;

public class Gusto {
    private Plato plato;
    private Restaurante restaurante;

    public Gusto(Plato plato, Restaurante restaurante) {
        this.plato = plato;
        this.restaurante = restaurante;
    }

    public Plato getPlato() { return plato; }

    public Restaurante getRestaurante() { return restaurante; }
}
